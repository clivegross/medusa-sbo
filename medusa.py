from app import app, models, checks, mapping, inbuildings, endpoints, views

models.db.create_all(bind='medusa')
app.run(debug=True, host='0.0.0.0')