from graphene import ObjectType, String, Schema, Int, List, Boolean, Enum, ID
from graphene.types.field import Field
from functools import cmp_to_key

from database import get_db
from models import Attack, Monster, Type, TypeEfficiency, Efficiency

class RankOrdering(Enum):
	ASC = "ASC"
	DESC = "DESC"

class Query(ObjectType):

	monster = Field(
		List(Monster),
		name=String(),
		id=List(ID),
		types=List(ID, description="IDs of types"),
		typeAnd=Boolean(default_value=True),

		rankOrdering=RankOrdering(),
		pageNr=Int(description="starts at 0"),
		pageSize=Int(default_value=20)
	)
	attack = Field(
		List(Attack),
		name=String(),
		id=List(ID),
		types=List(ID, description="IDs of types"),
		typeAnd=Boolean(default_value=True),

		pageNr=Int(description="starts at 0"),
		pageSize=Int(default_value=20)
	)
	type = Field(
		List(Type),
		name=String(),
		id=List(ID),

		pageNr=Int(description="starts at 0"),
		pageSize=Int(default_value=20)
	)
	typeEfficiency = Field(
		List(TypeEfficiency),
		fromTypes=List(ID, description="IDs of types"),
		toTypes=List(ID, description="IDs of types"),
		includeNormalEfficiency=Boolean(default_value=False, description="include not only efficiencies that are effective & not effective, also normal effectives")
	)

	def resolve_monster(root, info, typeAnd, pageSize, id=None, name=None, types=None, rankOrdering=None, pageNr=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id:
			questionMarks = ",".join(["?" for _ in id])
			whereFilter.add(f"id IN ({questionMarks})", *id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")

		if types:
			# build complex query
			typeIdQuestionmarks = ",".join(["?" for _ in types])
			selectMonsterTypes = f"SELECT monster_id AS id, type_id FROM monster_type WHERE type_id IN ({typeIdQuestionmarks})"
			filterByTypeNum = f"SELECT id, count(*) AS fittingTypes FROM ({selectMonsterTypes}) GROUP BY id HAVING fittingTypes = ?"
			selectMonsterId = f"SELECT id FROM ({filterByTypeNum})"

			# add as where clause
			whereFilter.add(f"id IN ({selectMonsterId})", *[*types, len(types) if typeAnd else 1])


		# build final query
		print(rankOrdering)
		orderByClause = "id" if not rankOrdering else f"rank {rankOrdering}"
		paginationClause = f"LIMIT {pageSize} OFFSET {pageNr * pageSize}" if pageNr is not None and pageNr >= 0 else ""
		MONSTER_SELECT_QUERY = "SELECT * FROM monster {} ORDER BY {} {}".format(whereFilter.getClause(), orderByClause, paginationClause)

		# execute query
		print(MONSTER_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(MONSTER_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_attack(root, info, typeAnd, pageSize, id=None, name=None, types=None, pageNr=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id:
			questionMarks = ",".join(["?" for _ in id])
			whereFilter.add(f"id IN ({questionMarks})", *id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")

		if types:
			# build complex query
			typeIdQuestionmarks = ",".join(["?" for _ in types])
			selectAttackTypes = f"SELECT attack_id AS id, type_id FROM attack_type WHERE type_id IN ({typeIdQuestionmarks})"
			filterByTypeNum = f"SELECT id, count(*) AS fittingTypes FROM ({selectAttackTypes}) GROUP BY id HAVING fittingTypes = ?"
			selectAttackId = f"SELECT id FROM ({filterByTypeNum})"

			# add as where clause
			whereFilter.add(f"id IN ({selectAttackId})", *[*types, len(types) if typeAnd else 1])

		# build final query
		paginationClause = f"LIMIT {pageSize} OFFSET {pageNr * pageSize}" if pageNr is not None and pageNr >= 0 else ""
		ATTACK_SELECT_QUERY = "SELECT * FROM attack {} ORDER BY id {}".format(whereFilter.getClause(), paginationClause)

		# execute query
		print(ATTACK_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(ATTACK_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_type(root, info, pageSize, id=None, name=None, pageNr=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if id:
			questionMarks = ",".join(["?" for _ in id])
			whereFilter.add(f"id IN ({questionMarks})", *id)

		if name: whereFilter.add("name LIKE ?", f"%{name}%")


		# build final query
		paginationClause = f"LIMIT {pageSize} OFFSET {pageNr * pageSize}" if pageNr is not None and pageNr >= 0 else ""
		TYPE_SELECT_QUERY = "SELECT * FROM type {} ORDER BY name {}".format(whereFilter.getClause(), paginationClause)

		# execute query
		print(TYPE_SELECT_QUERY, whereFilter.getArgs())
		result = conn.cursor().execute(TYPE_SELECT_QUERY, whereFilter.getArgs()).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


	def resolve_typeEfficiency(root, info, includeNormalEfficiency, fromTypes=None, toTypes=None):
		conn = get_db()
		whereFilter = WhereFilter()

		if fromTypes:
			questionMarks = ",".join(["?" for _ in fromTypes])
			whereFilter.add(f'"from" IN ({questionMarks})', *fromTypes)

		if toTypes:
			questionMarks = ",".join(["?" for _ in toTypes])
			whereFilter.add(f'"to" IN ({questionMarks})', *toTypes)

		parameterRenaming = 'id, "from" AS fromType, "to" AS toType, efficiency AS efficiencyValue'
		query = 'SELECT {} FROM type_efficiency {} ORDER BY "from", "to"'.format(parameterRenaming, whereFilter.getClause())
		result = get_db().cursor().execute(query, whereFilter.getArgs()).fetchall()

		print(query, whereFilter.getArgs())

		# convert list of result objects to list of dicts
		formattedResult = []
		for row in result:
			vals = dict(row)
			vals["efficiency"] = Efficiency.getValueFrom( vals["efficiencyValue"] )

			formattedResult.append(vals)

		if not includeNormalEfficiency: return formattedResult


		# add all missing relations and set their efficiency to normal (1.0)

		# get ids of ALL types from db, because we need them for either "fromType" or "toType" or both
		if not (fromTypes and toTypes):
			allIds = [dict(row)["id"] for row in get_db().cursor().execute('SELECT id FROM type').fetchall()]

			if not fromTypes: fromTypes = allIds
			if not toTypes: toTypes = allIds

		# get ids of all relations that have been solved by the db
		allRelations = {}
		for fromType in fromTypes: allRelations[fromType] = toTypes[:]	# shallow copy needed (not just reference)

		# remove already resolved (by db) from allRelations
		for row in formattedResult: allRelations[ row["fromType"] ].remove( row["toType"] )

		# add missing relations with efficiency normal
		missingRelations = []
		for fromType, toTypes in allRelations.items():
			for toType in toTypes:
				missingRelations.append({"id": -1, "fromType": fromType, "toType": toType, "efficiency": Efficiency.NORMAL_EFFECTIVE, "efficiencyValue": 1.0})

		# return both in a list, sorted by fromType and toType
		return sorted(formattedResult + missingRelations, key=cmp_to_key(sortByFromAndTo))


def sortByFromAndTo(relationA, relationB):
	fromA = relationA["fromType"]
	fromB = relationB["fromType"]
	if fromA != fromB: return fromA -fromB

	return relationA["toType"] - relationB["toType"]


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
