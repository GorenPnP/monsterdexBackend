from flask import Flask, request, g
from flask.json import jsonify
from flask_cors import CORS

from flask_graphql import GraphQLView

from schema import schema


app = Flask(__name__)
CORS(app)

# graphiql route on /graphiql
app.add_url_rule('/graphiql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


# send GET with ..?query={..}
@app.route("/", methods=["GET"])
def get_json():

	# If you return a dict from a view, it will be converted to a JSON response. Or use jsonify()
	return jsonify( schema.execute(request.args["query"]).data )



# close db connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
