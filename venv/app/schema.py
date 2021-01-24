from graphene import ObjectType, String, Schema, Int, List, Boolean, Enum
from graphene.types.field import Field

from .database import get_db
from .models import Attack, Monster, Type, TypeEfficiency

class RankOrdering(Enum):
	ASC = "ASC",
	DESC = "DESC"

class Query(ObjectType):

	monster = Field(
		List(Monster),
		name=String(),
		id=Int(),
		types=List(Int),
		typeAnd=Boolean(default_value=True),
		rankOrdering=RankOrdering()
	)
	attack = Field(
		List(Attack),
		name=String(),
		id=Int(),
		types=List(Int),
		typeAnd=Boolean(default_value=True)
	)
	type = Field(
		List(Type),
		name=String(),
		id=Int()
	)
	typeEfficiency = Field(
		TypeEfficiency,
		fromType=Int(name="from", required=True),
		toType=Int(name="to", required=True)
	)

	def resolve_monster(root, info, typeAnd, id=None, name=None, types=None, rankOrdering=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id: whereFilter.add("id = ?", id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")

		if types:
			# build complex query
			typeIdQuestionmarks = ",".join(["?" for _ in types])
			selectMonsterTypes = f"SELECT monster_id as id, type_id FROM monster_type WHERE type_id IN ({typeIdQuestionmarks})"
			filterByTypeNum = f"SELECT id, count(*) as fittingTypes FROM ({selectMonsterTypes}) GROUP BY id HAVING fittingTypes = ?"
			selectMonsterId = f"SELECT id FROM ({filterByTypeNum})"

			# add as where clause
			whereFilter.add(f"id IN ({selectMonsterId})", *[*types, len(types) if typeAnd else 1])
		
		# build final query
		orderByClause = "id" if not rankOrdering else f"rank {rankOrdering[0]}"
		MONSTER_SELECT_QUERY = "SELECT * FROM monster {} ORDER BY {}".format(whereFilter.getClause(), orderByClause)
		
		# execute query
		print(MONSTER_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(MONSTER_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_attack(root, info, typeAnd, id=None, name=None, types=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id: whereFilter.add("id = ?", id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")

		if types:
			# build complex query
			typeIdQuestionmarks = ",".join(["?" for _ in types])
			selectAttackTypes = f"SELECT attack_id as id, type_id FROM attack_type WHERE type_id IN ({typeIdQuestionmarks})"
			filterByTypeNum = f"SELECT id, count(*) as fittingTypes FROM ({selectAttackTypes}) GROUP BY id HAVING fittingTypes = ?"
			selectAttackId = f"SELECT id FROM ({filterByTypeNum})"

			# add as where clause
			whereFilter.add(f"id IN ({selectAttackId})", *[*types, len(types) if typeAnd else 1])
		
		# build final query
		ATTACK_SELECT_QUERY = "SELECT * FROM attack {} ORDER BY id".format(whereFilter.getClause())
		
		# execute query
		print(ATTACK_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(ATTACK_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_type(root, info, id=None, name=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id: whereFilter.add("id = ?", id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")


		# build final query
		TYPE_SELECT_QUERY = "SELECT * FROM type {} ORDER BY name".format(whereFilter.getClause())
		
		# execute query
		print(TYPE_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(TYPE_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]

	
	def resolve_typeEfficiency(root, info, fromType, toType):
		conn = get_db()
		query = 'SELECT * FROM type_efficiency where "from" = ? AND "to" = ?'
		result = get_db().cursor().execute(query, [fromType, toType]).fetchall()

		# convert list of result objects to list of dicts
		return dict(result[0]) if result else {'from': fromType, 'to': toType, 'efficiency': 1.0}

"""
facilitates filtering with a WHERE-clause with changing, multiple parameters
"""
class WhereFilter:

	def __init__(self):
		self.clear()

	def clear(self):
		self.clauses = []
		self.args = []

	def add(self, clause, *args):

		if clause.count("?") != len(args):
			raise Exception("Number of arguments does not match number of '?' in where-clause")

		self.clauses.append(clause)
		for arg in args: self.args.append(arg)

	def getClause(self):
		return " WHERE " + " AND ".join(self.clauses) if self.clauses else ""

	def getArgs(self):
		return self.args


schema = Schema(query=Query)
