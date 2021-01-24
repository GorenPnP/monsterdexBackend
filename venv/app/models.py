from app.database import get_db
from graphene import ObjectType, String, Int, Float, List, Field


class Type(ObjectType):

	id = Int()
	name = String()


class TypeEfficiency(ObjectType):
	fromType = Int(name="from")
	toType = Int(name="to")
	efficiency = Float()


class Attack(ObjectType):

	id = Int()
	name = String()
	damage = String()
	description = String()

	types = List(of_type=Type)

	def resolve_types(self, info):

		query = '''
			select * from type where id IN (
				select type_id from attack_type where attack_id=?
			)'''
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]


class Monster(ObjectType):

	id = Int()
	name = String()
	rank = Int()
	height = Float()
	hp = Int()
	habitat = String()
	description = String()
	damage_prevention = String()
	weight = Float()

	# forms = List(of_type=Monster)
	# evolution_pre = Field(Monster)
	# evolution_after = Field(Monster)

	types = List(of_type=Type)
	attacks = List(of_type=Attack)

	def resolve_types(self, info):

		query = '''
			select * from type where id IN (
				select type_id from monster_type where monster_id=?
			)'''
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]

	def resolve_attacks(self, info):

		query = '''
			select * from attack where id IN (
				select attack_id from monster_attack where monster_id=?
			)'''
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row) for row in result]
