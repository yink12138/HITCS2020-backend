from flask import Flask
import blueprint


app = Flask(__name__)
app.register_blueprint(blueprint.auth, url_prefix='/api/auth')
app.register_blueprint(blueprint.info, url_prefix='/api/info')


app.run(host="0.0.0.0", port=8081)
