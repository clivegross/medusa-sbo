from app import app, db, registry
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, Result, LoggedEntity, LogTimeValue, IssueHistory, IssueHistoryTimestamp, InbuildingsConfig, Email
from app.models import Alarm
from app.forms import SiteConfigForm, AddSiteForm
from flask import json, request, render_template, url_for, redirect, jsonify, flash, make_response
from flask_user import current_user
from statistics import mean
import datetime, time


# enforce login required for all pages
@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated

    if (request.endpoint and
        # not required for login page or static content
        request.endpoint != 'user.login' and
        request.endpoint != 'static' and
        not login_valid and
        # check if it's allowed to be public, see public_endpoint decorator
        not getattr(app.view_functions[request.endpoint], 'is_public', False    ) ) :
        # redirect to login page if they are not authenticated
        return redirect(url_for('user.login'))

# decorator to make pages not require login
def public_endpoint(function):
    function.is_public = True
    return function


###################################
## main pages for all sites
###################################

# default path
@app.route('/')
def main():
    return redirect(url_for('homepage_all'))

# set homepage for overall view
@app.route('/site/all')
def homepage_all():
    return redirect(url_for('dashboard_all'))

# show overview dashboard. has aggregated info for all the sites that are attached to the currently logged in user
@app.route('/site/all/dashboard')
def dashboard_all():
    sites = current_user.sites
    # sqlalchemy can't do relationship filtering to see if an attribute is in a list of objects (e.g. to see if asset.site is in sites)
    # instead, we do the filtering on the ids (e.g. to see if asset.site.id is in the list of site ids)
    site_ids = [site.id for site in sites]
    # get only results that are active or unacknowledged
    # needs to be joined to the site table to do filtering on the site id
    results = Result.query.join(Result.asset).join(Asset.site).filter((Result.active == True) | (Result.acknowledged == False), Site.id.in_(site_ids)).order_by(Asset.priority.asc()).all()
    num_results = len(results)

    if num_results == 0:
        # there are no issues across any sites. Celebrate!
        top_priority = "-"
    else:
        top_priority = results[0].asset.priority

    # join to site table to allow filtering by site id
    if len(Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()) > 0:
        try:
            avg_health = mean([asset.health for asset in Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()])
        except TypeError:
            # one of the asset healths is Null, so set it to zero
            for asset in Asset.query.all():
                if asset.health is None:
                    asset.health = 0
            db.session.commit()
            avg_health = mean([asset.health for asset in Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()])

    else:
        avg_health = 0

    # get alarms display data

    nalarms = "FAIL"
    # get database session for this site
    try:
        nalarms = get_alarms_per_week(db.session, nweeks=8)

    except Exception as e:
        message = "No data. " + str(e)

    # join to site table to allow filtering by site id
    low_health_assets = len(Asset.query.join(Asset.site).filter(Asset.health < 0.5, Site.id.in_(site_ids)).all())
    # only send results[0:5], to display the top 5 priority issues in the list
    return render_template('dashboard.html', results=results[0:5], num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, allsites=True, alarmcount=nalarms)

# list all sites that are attached to the logged in user
@app.route('/site/all/sites')
def site_list():
    sites = current_user.sites
    issues = {}
    priority = {}
    for site in sites:
        issues[site.name] = len(site.get_unresolved())
        if not site.get_unresolved_by_priority():
            # there are no issues at this site
            top_priority = "-"
        else:
            top_priority = site.get_unresolved_by_priority()[0].asset.priority
        priority[site.name] = top_priority
    return render_template('sites.html', sites=sites, issues=issues, priority=priority, allsites=True)

# list all unresolved issues for the sites attached to the logged in user
@app.route('/site/all/issues')
def unresolved_list_all():
    sites = current_user.sites
    results = []
    for site in sites:
        results.extend(site.get_unresolved())
    return render_template('issues.html', results=results, allsites=True)

# handle update from acknowledging/editing notes of issues for all issues
@app.route('/site/all/issues/_submit', methods=['POST'])
def unresolved_issues_submit_all():
    sites = current_user.sites
    results = []
    for site in sites:
        results.extend(site.get_unresolved())

    # unacknowledge all results and set notes field
    for result in results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('unresolved_list_all'))

# display chart of unresolved issues over time
@app.route('/site/all/issue-chart')
def unresolved_chart():
    sites = current_user.sites
    history = IssueHistoryTimestamp.query.filter(IssueHistoryTimestamp.timestamp > datetime.datetime.now()-datetime.timedelta(hours=24)).all()

    # generate array to be converted into chart
    # currently just builds a string character by character, can probably be done better
    # header row, contains the x axis label followed by the name of each site
    array = "[['Time',"
    for site in sites:
        array += "'" + site.name + "',"
    array += "],"
    # data rows. each row starts with a timestamp, followed by the issue counts for each site at that time
    for timestamp in history:
        array += "[new Date(" + str(date_to_millis(timestamp.timestamp)) + "),"
        for site in sites:
            # if issues were not recorded for a site at a particular timestamp, use a value of 0
            issues_temp = 0
            for issues in timestamp.issues:
                if (site == issues.site):
                    issues_temp = issues.issues
            array += str(issues_temp) + ","
        array += "],"
    array += "]"

    return render_template('issue_chart.html', sites=sites, array=array, history=history, allsites=True)

# show map of all tech locations
# NOTE: currently just set to iframe a blank google maps
@app.route('/site/all/map')
def map():
    # TODO: figure out how to auto sign into the inbuildings page. Attempt at cookies below doesn't work
    response = make_response(render_template('map.html', allsites=True))
    response.set_cookie('ARRAffinity', 'd5fb9e944f8abbefd6bc0a9a39c159ffc6fbb4084e000bed662582769266cb00', domain='.inbuildings.info')
    response.set_cookie('PHPSESSID', 'pudr7sj47olg948h1ollv8vrv7', domain='inbuildings.info')
    return response

# conversion tool for adding entries to the issue chart
# necessary to match python date format to javascript date format
@app.template_filter('date_to_millis')
def date_to_millis(d):
    """Converts a datetime object to the number of milliseconds since the unix epoch."""
    return int(time.mktime(d.timetuple())) * 1000

# handle creation of a new site
@app.route('/site/all/add_site', methods=['GET', 'POST'])
def add_site():

    form = AddSiteForm()

    if request.method == 'GET':
        return render_template('add_site.html', form=form, allsites=True)

    elif request.method == 'POST':
        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('add_site.html', form=form, allsites=True)

        site = Site(name=form.name.data)
        # generate cmms config object for the new site (currently only inbuildings)
        site.inbuildings_config = InbuildingsConfig(enabled=False, key="")

        # convert port input to a string
        # if blank it will be recorded as 'None', so manually set empty string
        if form.db_port.data is None:
            form.db_port.data = ""
        form.db_port.data = str(form.db_port.data)

        # update webreports database settings
        form.populate_obj(site)
        site.generate_key()

        db.session.add(site)
        db.session.commit()
        return redirect(url_for('add_asset', sitename=site.name))

###################################
## main pages for single site
###################################

# set homepage for the site
@app.route('/site/<sitename>')
def homepage(sitename):

    return redirect(url_for('dashboard_site', sitename=sitename))

# show site overview dashboard
@app.route('/site/<sitename>/dashboard')
def dashboard_site(sitename):
    site = Site.query.filter_by(name=sitename).one()
    # only show the top 5 issues by priority in the list
    results = site.get_unresolved_by_priority()[0:4]
    num_results = len(site.get_unresolved())

    if not site.get_unresolved_by_priority():
        # no issues at this site
        top_priority = "-"
    else:
        top_priority = site.get_unresolved_by_priority()[0].asset.priority

    if len(site.assets) > 0:
        try:
            avg_health = mean([asset.health for asset in site.assets])
        except TypeError:
            # one of the asset healths is Null, so fix and set to 0
            for asset in site.assets:
                if asset.health is None:
                    asset.health = 0
            db.session.commit()
            avg_health = mean([asset.health for asset in site.assets])
    else:
        avg_health = 0

    # count the number of assets with <50% health
    low_health_assets = len(Asset.query.filter(Asset.site == site, Asset.health < 0.5).all())

    # get alarms display data
    site = Site.query.filter_by(name=sitename).one()
    nalarms = "FAIL"
    # get database session for this site
    try:
        # NEED TO FILTER THIS BY SITE ID!
        alarms = db.session.query(Alarm).limit(20).all()
        alarm_names = [alarm.AlarmText for alarm in alarms]
        nalarms = get_alarms_per_week(db.session, nweeks=8)

    except Exception as e:
        message = "Site not connected." + str(site.name) + '\n' + str(e)

    return render_template(
        'dashboard.html',
        results=results,
        num_results=num_results,
        top_priority=top_priority,
        avg_health=avg_health,
        low_health_assets=low_health_assets,
        site=site,
        alarmcount=nalarms
    )

# list assets on the site
@app.route('/site/<sitename>/assets',  methods=['GET', 'POST'])
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    asset_quantity = {}
    for asset_type in asset_types:
        asset_quantity[asset_type.name] = len(Asset.query.filter_by(site=site, type=asset_type).all())
    return render_template('assets.html', assets=site.assets, asset_quantity=asset_quantity, asset_types=asset_types, site=site)

# list unresolved issues on the site
@app.route('/site/<sitename>/issues')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()
    return render_template('issues.html', results=results, site=site)

# handle update from acknowledging/editing notes of issues for a site
@app.route('/site/<sitename>/issues/_submit', methods=['POST'])
def unresolved_issues_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()

    # unacknowledge all results and set notes field
    for result in results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('unresolved_list', sitename=sitename))

# show details for a single asset
@app.route('/site/<sitename>/details/<asset_id>')
def asset_details(sitename, asset_id):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(id=asset_id).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()
    algorithms = set(asset.algorithms) - set(asset.exclusions)
    return render_template('asset_details.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results, algorithms=algorithms)

# handle update from acknowledging/editing notes of issues for a single asset
@app.route('/site/<sitename>/results/<asset_id>/_submit', methods=['POST'])
def asset_issues_submit(sitename, asset_id):
    asset = Asset.query.filter_by(id=asset_id).one()
    unresolved_results = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()

    # unacknowledge all results and set notes field
    for result in unresolved_results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('asset_details', sitename=sitename, asset_id=asset_id))

# site config page
@app.route('/site/<sitename>/config', methods=['GET','POST'])
def site_config(sitename):
    site = Site.query.filter_by(name=sitename).one()
    inbuildings_config = InbuildingsConfig.query.filter_by(site=site).one()

    if request.method == 'POST':
        form = SiteConfigForm()

        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('site_config.html', inbuildings_config=inbuildings_config, site=site, form=form)

        # convert port input to a string
        if form.db_port.data is None:
            form.db_port.data = ""
        form.db_port.data = str(form.db_port.data)

        # update webreports database settings
        form.populate_obj(site)
        site.generate_key()

        # update inbuildings settings
        inbuildings_config.enabled = form.inbuildings_enabled.data
        inbuildings_config.key = form.inbuildings_key.data

        # update emails
        emails = []
        # remove whitespace and separate out emails from csv
        email_strings = set(form.email_list.data.replace(" ", "").split(','))
        for email_string in email_strings:
            if email_string != '':
                emails.append(Email(address=email_string))
        site.emails = emails

        db.session.commit()
        return redirect(url_for('homepage', sitename=sitename))

    elif request.method == 'GET':
        # prefill form with information from site object
        form = SiteConfigForm(obj=site)
        form.inbuildings_enabled.data = inbuildings_config.enabled
        form.inbuildings_key.data = inbuildings_config.key
        # turn emails into csv
        form.email_list.data = ','.join([email.address for email in site.emails])
        return render_template('site_config.html', site=site, form=form)


# TESTING ALARMS CG

def get_alarms_per_week(session, nweeks=4):
    """
    get all alarm records per week from today until nweeks

    return a list:
    [
        [dt1, nalarms1],
        [dt2, nalarms2],
        ...
    ]

    TODO:
    - move this to "alarms functions and algos module"
    - migrate to a class for handling alarm lists
    - allow more flexibility to include unacknowledged etc

    """
    end_date = datetime.date.today()
    series = []
    for i in range(nweeks):
        start_date = end_date - datetime.timedelta(days=7)
        # count number of alarms in range
        nalarms = db.session.query(Alarm).filter(
            Alarm.DateTimeStamp > start_date,
            Alarm.DateTimeStamp <= end_date
        ).count()
        series.append([start_date.strftime("%-d-%b"), nalarms])
        # get the next earliest week next loop
        end_date = start_date
    # reverse order
    series.reverse()
    # number of alarms
    return series

# return table of alarms
@app.route('/site/<sitename>/alarms')
def return_alarms(sitename):

    site = Site.query.filter_by(name=sitename).one()

    message = "squirrel"
    alarm_names = []
    nalarms = "FAIL"
    # get database session for this site
    try:
        alarms = db.session.query(Alarm).limit(20).all()
        alarm_names = [alarm.AlarmText for alarm in alarms]
        nalarms = get_alarms_per_week(db.session, nweeks=8)

    except Exception as e:
        message = "Site not connected." + str(site.name) + '\n' + str(e)


    return render_template(
        'alarms.html',
        site=site,
        message=message,
        alarms=alarm_names,
        nalarms=nalarms,
	    rows=nalarms
    )
