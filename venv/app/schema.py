from graphene import ObjectType, String, Schema, Int, List
from graphene.types.field import Field

from .database import get_db
from .models import Attack, Monster, Type


class Query(ObjectType):
	hello = String(
		name=String(default_value="You"),
		age=Int(default_value=18)
	)
	goodbye = String()


	monster = Field(
		List(Monster),
		name=String(),
		id=Int()
	)
	attack = Field(
		List(Attack),
		name=String(),
		id=Int()
	)
	type = Field(
		List(Type),
		name=String(),
		id=Int()
	)

	def resolve_hello(root, info, name=None, age=None):
		return 'Hello {} ({})!'.format(name, age)

	def resolve_goodbye(root, info):
		return 'See ya!'

	def resolve_monster(root, info, id=None, name=None):
		conn = get_db()
		table = "monster"
		where_clauses = []
		args = []

		if id:
			where_clauses.append("id = ?")
			args.append(id)

		if name:
			where_clauses.append("name = ?")
			args.append(name)

		# add "WHERE" to the first element if there is one
		if where_clauses:
			where_clauses[0] = "WHERE " + where_clauses[0]

		print("SELECT * FROM {} {}".format(table, " AND ".join(where_clauses)))
		result = conn.cursor().execute("SELECT * FROM {} {}".format(table, " AND ".join(where_clauses))  , args).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_attack(root, info, id=None, name=None):
		conn = get_db()
		result = conn.cursor().execute("SELECT * FROM attack;").fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_type(root, info, id=None, name=None):
		conn = get_db()
		result = conn.cursor().execute("SELECT * FROM type;").fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


schema = Schema(query=Query)
