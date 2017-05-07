from app import db, app
from sqlalchemy import orm, create_engine, event
from sqlalchemy.engine.url import make_url
from flask import _app_ctx_stack
from flask_sqlalchemy import SignallingSession
import sys, datetime
from app.models.StruxureWareReportsDB import Alarm

###################################
## models in report server database
###################################

# stores a session for each WebReports server. Configured to match default Flask-SQLAlchemy configs
# IMPORTANT this does not use default Flask-SQLAlchemy behaviour. WebReports models must be referenced as
# session.query(LogTimeValue) or session.query(LoggedEntity) rather than LogtimeValue.query
class SessionRegistry(object):
    _registry = {}

    def get(self, url):
        try:
            # reuse scoped_sessions if they already exist for that database, otherwise create one
            if url not in self._registry:

                # existing Flask-SQLAlchemy settings
                options = {'convert_unicode': True}
                echo = app.config['SQLALCHEMY_ECHO']
                if echo:
                    options['echo'] = echo
                engine = create_engine(make_url(url), **options)
                session_factory = orm.sessionmaker(bind=engine, autocommit=False, autoflush=True, query_cls=db.Query)

                # scoped session handles serving same/different session depending on which thread is calling
                # scoped to a each web request
                session = orm.scoped_session(session_factory, scopefunc=_app_ctx_stack.__ident_func__)
                self._registry[url] = session

            # trigger an event to check database connection
            self._registry[url].commit()
            #print(self._registry[url].bind.pool.status())
            return self._registry[url]

        # return empty session if it can't connect
        except:
            return None

# failsafe function to close sessions at the end of web request. does not work for sessions generated by scheduler
@app.teardown_appcontext
def shutdown_sessions(exception=None):
    from app import registry
    for session in registry._registry.values():
        session.remove()


# trend log values, stored in report server
class LogTimeValue(db.Model):
    __tablename__ = 'tbLogTimeValues'
    datetimestamp = db.Column('DateTimeStamp',db.DateTime)
    seqno = db.Column('SeqNo',db.BigInteger,primary_key=True)
    float_value = db.Column('FloatVALUE',db.Float)
    parent_id = db.Column('ParentID',db.Integer,primary_key=True)
    odometer_value = db.Column('OdometerValue',db.Float)

# list of trend logs, stored in report server
class LoggedEntity(db.Model):
    __tablename__ = 'tbLoggedEntities'
    id = db.Column('ID',db.Integer,primary_key=True)
    guid = db.Column('GUID',db.String(50))
    path = db.Column('Path',db.String(1024))
    descr = db.Column('Descr',db.String(512))
    disabled = db.Column('Disabled',db.Boolean)
    last_mod = db.Column('LastMod',db.DateTime)
    version = db.Column('Version',db.Integer)
    type = db.Column('Type',db.String(80))
    log_point = db.Column('LogPoint',db.String(1024))
    unit_prefix = db.Column('UNITPREFIX',db.String(512))
    unit = db.Column('Unit',db.String(512))
    base_value = db.Column('BaseValue',db.Float)
    meter_startpoint = db.Column('MeterStartPoint',db.Float)
    last_read_value = db.Column('LastReadValue',db.Float)

###################################
## abstract models
###################################

# many-many mapping table between algorithms and the point types they require
algo_point_mapping = db.Table('algo_point_mapping',
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
    db.Column('Point_type_id', db.Integer, db.ForeignKey('point_type.ID'), primary_key=True),
)

# many-many mapping table between algorithms and the functional descriptors they require
algo_function_mapping = db.Table('algo_function_mapping',
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
    db.Column('FunctionalDescriptor_id', db.Integer, db.ForeignKey('functional_descriptor.ID'), primary_key=True),
)

# asset types
class AssetType(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512), nullable=False)
    assets = db.relationship('Asset', backref='type')
    functions = db.relationship('FunctionalDescriptor', backref='type')

    def __repr__(self):
        return self.name

# functional descriptors
class FunctionalDescriptor(db.Model):
    id = db.Column('ID',db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512), nullable=False)
    type_id = db.Column('Type_id', db.Integer, db.ForeignKey('asset_type.ID'))

    def __repr__(self):
        return self.name

# point types
class PointType(db.Model):
    id = db.Column('ID',db.Integer, primary_key=True)
    name = db.Column('Name',db.String(512), nullable=False)
    asset_points = db.relationship('AssetPoint', backref='type')

    def __repr__(self):
        return self.name

# algorithms. the 'name' field refers to the actual algorithm classname in the code
class Algorithm(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    descr = db.Column('Descr', db.String(512))
    is_mapped = db.Column('Is_mapped', db.Boolean)
    point_types = db.relationship('PointType', secondary=algo_point_mapping, backref=db.backref('algorithms'))
    functions = db.relationship('FunctionalDescriptor', secondary=algo_function_mapping, backref=db.backref('algorithms'))
    results = db.relationship('Result', backref='algorithm')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_on_load()
        self.map()

    # this triggers when loading from the db
    @orm.reconstructor
    def init_on_load(self):
        # find the corresponding class in the code that matches the 'name' field
        self.algorithm = getattr(sys.modules['app.algorithms.algorithms'], self.name)

    # call the code from the actual algorithm
    def run(self, *args, **kwargs):
        return self.algorithm.run(*args, **kwargs)

    # update mappings to point types and assets
    def map(self):
        try:
            # update required point types based on specified point_type attribute in .algorithm
            self.point_types.clear()
            for point_type_reqd in self.algorithm.points_required:
                point_type = PointType.query.filter_by(name=point_type_reqd).one()
                self.point_types.append(point_type)

            # update required functional descriptors
            self.functions.clear()
            for function_reqd in self.algorithm.functions_required:
                function = FunctionalDescriptor.query.filter_by(name=function_reqd).one()
                self.functions.append(function)

            self.is_mapped = True

        # the point or functional descriptor required for the algorithm is not defined
        except:
            self.assets.clear()
            self.is_mapped = False
            return

        # update asset mappings
        self.assets.clear()
        for asset in Asset.query.all():
            asset.map_algorithm(self)

    def __repr__(self):
        return self.name

# templates for emails. stored as strings
class EmailTemplate(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    title = db.Column('Title', db.String(1024))
    body = db.Column('Body', db.Text)

###################################
## real world models
###################################

# many-many mapping table between assets and the functional descriptors that apply to them
asset_function_mapping = db.Table('asset_function_mapping',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True),
    db.Column('FunctionalDescriptor_id', db.Integer, db.ForeignKey('functional_descriptor.ID'), primary_key=True),
)

# many-many mapping table between assets and the algorithms that apply to them
algo_asset_mapping = db.Table('algo_asset_mapping',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True),
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
)

# many-many mapping table defining algorithms that are excluded from operating on an assets
algo_exclusions = db.Table('algo_exclusions',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True),
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
)

# many-many mapping table defining which points were checked for each algorithm result
points_checked = db.Table('points_checked',
    db.Column('Result_id', db.Integer, db.ForeignKey('result.ID'), primary_key=True),
    db.Column('Point_id', db.Integer, db.ForeignKey('asset_point.ID'), primary_key=True),
)

# list of customer sites
class Site(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512), nullable=False)
    db_key = db.Column('DB_key', db.String(512), default="")
    db_username = db.Column('DB_username', db.String(512), default="")
    db_password = db.Column('DB_password', db.String(512), default="")
    db_address = db.Column('DB_address', db.String(512), default="")
    db_port = db.Column('DB_port', db.String(512), default="")
    db_name = db.Column('DB_name', db.String(512), default="")
    email_trigger_priority = db.Column('Email_trigger_priority', db.Integer)
    cmms_trigger_priority = db.Column('CMMS_trigger_priority', db.Integer)
    assets = db.relationship('Asset', backref='site')
    inbuildings_assets = db.relationship('InbuildingsAsset', backref='site')
    inbuildings_config = db.relationship('InbuildingsConfig', backref='site', uselist=False)
    issue_history = db.relationship('IssueHistory', backref='site')

    def __repr__(self):
        return self.name

    def generate_key(self):
        self.db_key = ''.join(['mssql+pymssql://', self.db_username, ':', self.db_password, '@', self.db_address, ':', self.db_port, '/', self.db_name])

    def get_unresolved(self):
        issues = Result.query.join(Result.asset).filter((Result.active == True) | (Result.acknowledged == False), Asset.site == self).all()
        return issues

    def get_unresolved_by_priority(self):
        issue = Result.query.join(Result.asset).filter((Result.active == True) | (Result.acknowledged == False), Asset.site == self).order_by(Asset.priority.asc()).all()
        return issue

# data pulled from inbuildings
class InbuildingsAsset(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    location = db.Column('Location', db.String(512))
    group = db.Column('Group', db.String(512))
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'))
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'))

    def __repr__(self):
        return self.name

# list of assets
class Asset(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('Name', db.String(512), nullable=False)
    location = db.Column('Location', db.String(512), default="")
    group = db.Column('Group', db.String(512), default="")
    health = db.Column('Health', db.Float, default=0, nullable=False)
    priority = db.Column('Priority', db.Integer, default=0, nullable=False)
    notes = db.Column('Notes', db.Text, default="")
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)
    type_id = db.Column('Type_id', db.Integer, db.ForeignKey('asset_type.ID'), nullable=False)
    points = db.relationship('AssetPoint', backref='asset', cascade='save-update, merge, delete, delete-orphan')
    results = db.relationship('Result', backref='asset', cascade='save-update, merge, delete, delete-orphan')
    inbuildings = db.relationship('InbuildingsAsset', backref='asset', uselist=False)
    exclusions = db.relationship('Algorithm', secondary=algo_exclusions, backref='exclusions')
    algorithms = db.relationship('Algorithm', secondary=algo_asset_mapping, backref='assets')
    functions = db.relationship('FunctionalDescriptor', secondary=asset_function_mapping, backref='assets')

    # update the mapping between this asset and all algorithms
    def map(self):
        # delete the current mapping
        self.algorithms.clear()
        for algorithm in Algorithm.query.all():
            self.map_algorithm(algorithm)

    # map this asset to a single algorithm based on previously generated relationship between asset-point_types-algorithms
    def map_algorithm(self, algorithm):
        if algorithm.is_mapped == True:
            passed = True
            # check the points required by algorithm against the points the asset actually has
            for point in algorithm.point_types:
                if not point in self.get_point_types():
                    passed = False

            # check the functional descriptors required by algorithm against the functional descriptors the asset actually has
            for function in algorithm.functions:
                if not function in self.functions:
                    passed = False

            # if all are matching, add the relationship
            if passed == True:
                self.algorithms.append(algorithm)

    def get_point_types(self):
        return [point.type for point in self.points]

    def __repr__(self):
        return self.name

# points that each asset has - there may be multiple of the same type
class AssetPoint(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True, autoincrement=True)
    name = db.Column('Name', db.String(512), nullable=False)
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), nullable=False)
    type_id = db.Column('PointType_id', db.Integer, db.ForeignKey('point_type.ID'), nullable=False)
    loggedentity_id = db.Column('LoggedEntity_id', db.Integer)

    def __repr__(self):
        if not self.name is None:
            return self.name
        else:
            return "Unnamed - {}".format(self.type.name)

# timestamped list containing the results of all algorithms ever applied to each asset
class Result(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    first_timestamp = db.Column('First_timestamp', db.DateTime, default=datetime.datetime.now(), nullable=False)
    recent_timestamp = db.Column('Recent_timestamp', db.DateTime, default=datetime.datetime.now(), nullable=False)
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), nullable=False)
    algorithm_id = db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), nullable=False)
    value = db.Column('Result', db.Float, default=0, nullable=False)
    passed = db.Column('Passed', db.Boolean)
    priority = db.Column('Priority', db.Integer, nullable=False)
    active = db.Column('Active', db.Boolean, default=True)
    acknowledged = db.Column('Acknowledged', db.Boolean, default=False)
    occurances = db.Column('Occurances', db.Integer, default=1, nullable=False)
    recent = db.Column('Recent', db.Boolean, default=True)
    notes = db.Column('Notes', db.Text, default="")
    points = db.relationship('AssetPoint', secondary=points_checked, backref='results')

    def __repr__(self):
        return str(self.timestamp) + " - " + self.algorithm.name

    @classmethod
    def get_unresolved(cls):
        issues = cls.query.filter((cls.active == True) | (cls.acknowledged == False)).all()
        return issues

    @classmethod
    def get_unresolved_by_priority(cls):
        issue = cls.query.join(cls.asset).filter((cls.active == True) | (cls.acknowledged == False)).order_by(Asset.priority.asc()).all()
        return issue

# config properties for Inbuildings interface
class InbuildingsConfig(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)
    enabled = db.Column('Enabled', db.Boolean, default=False)
    key = db.Column('Connection_key', db.String(512), default="")


###################################
## charting info
###################################

# table of timestamps. Simplifies graphing if IssueHistory for different sites is grouped under the same timestamp object
class IssueHistoryTimestamp(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    timestamp = db.Column('Timestamp', db.DateTime, nullable=False)
    issues = db.relationship('IssueHistory', backref='timestamp')

# timestamped list containing the quantity of issues present at each site over time
class IssueHistory(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    issues = db.Column('Issues', db.Integer, nullable=False)
    timestamp_id = db.Column('Timestamp_id', db.Integer, db.ForeignKey('issue_history_timestamp.ID'), nullable=False)
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)


###################################
## helper functions
###################################

# function to re-map an asset whenever it is updated. Attaches to SignallingSession, which is the base for db.session
@event.listens_for(SignallingSession, 'before_flush')
def map_asset_on_update(session, flush_context, instances):
    changes = set(session.new) | set(session.dirty) | set(session.deleted)
    # check if any of the changes being commited are assets
    changed_assets = [change for change in changes if isinstance(change, Asset)]
    # check for changes to asset points, and add their corresponding asset to the list
    changed_assets.extend([change.asset for change in changes if isinstance(change, AssetPoint)])
    # remove duplicates
    changed_asset_set = set(changed_assets)
    # if somehow a null object got in here, remove it
    changed_asset_set.discard(None)

    for asset in changed_asset_set:
        asset.map()
