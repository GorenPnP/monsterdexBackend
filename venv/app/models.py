from database import get_db
from graphene import ObjectType, String, Int, Float, List, Field, ID, Enum
from PIL import Image

from io import BytesIO
import base64, os
from pathlib import Path

class Efficiency(Enum):
	VERY_EFFECTIVE = 2.0,
	NOT_EFFECTIVE = 0.5,
	DOES_NOT_HIT = -1.0,
	NORMAL_EFFECTIVE = 1.0

	@classmethod
	def getValueFrom(cls, floatVal):
		""" TODO is there a better way? """

		if floatVal == 2.0: return Efficiency.VERY_EFFECTIVE
		if floatVal == 0.5: return Efficiency.NOT_EFFECTIVE
		if floatVal == -1.0: return Efficiency.DOES_NOT_HIT
		if floatVal == 1.0: return Efficiency.NORMAL_EFFECTIVE

		raise Error(f"No enum member for {floatVal} found")


class Type(ObjectType):
	id = ID()
	name = String()


class TypeEfficiency(ObjectType):
	fromType = ID()
	toType = ID()
	efficiency = Efficiency()
	efficiencyValue = Float(description="EfficiencyValue of 2.0: very effective, 0.5: not effective, -1: does not hit at all, 1.0: normal effective")


class Attack(ObjectType):

	id = ID()
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

	thumbnail = String(description="size suited for thumbnails, is a base64 png image")
	image = String(description="size suited for larger formats, is a base64 png image")

	id = ID()
	name = String()
	rank = Int()
	height = Float(description="in meters")
	hp = Int()
	habitat = String()
	description = String()
	damage_prevention = String()
	weight = Float(description="in kilograms")

	forms = List(of_type=ID, description="IDs of monsters")
	opposite = List(of_type=ID, description="IDs of monsters")
	evolution_pre = List(of_type=ID, description="IDs of monsters")
	evolution_after = List(of_type=ID, description="IDs of monsters")

	types = List(of_type=Type)
	attacks = List(of_type=Attack)

	def resolve_thumbnail(self, info):
		max_size = 128, 128
		id = self.get("id")
		
		return _get_resized_png(id, max_size)

	def resolve_image(self, info):
		max_size = 1024, 1024
		id = self.get("id")

		return _get_resized_png(id, max_size)

	def resolve_forms(self, info):
		query = "select mon_2 from monster_forms where mon_1 = ? ORDER BY mon_2"
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row)["mon_2"] for row in result]

	def resolve_opposite(self, info):
		query = "select mon_2 from monster_opposite where mon_1 = ? ORDER BY mon_2"
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row)["mon_2"] for row in result]

	def resolve_evolution_pre(self, info):
		query = 'select "from" from monster_evolution where "to" = ? ORDER BY "from"'
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row)["from"] for row in result]

	def resolve_evolution_after(self, info):
		query = 'select "to" from monster_evolution where "from" = ? ORDER BY "to"'
		result = get_db().cursor().execute(query, [self.get("id")]).fetchall()

		# convert list of result objects to list of dicts
		return [dict(row)["to"] for row in result]

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


def _get_resized_png(monster_id: int, max_size: (int, int)): # max_size = (width, height) in px

	# safe from injecting paths to read the filesystem
	if type(monster_id) is not int: return ''

	# need a few paths ..
	path_of_original_images = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../static/monster_images/")
	path_of_scaled_images = os.path.join(path_of_original_images, f"{max_size[0]}_{max_size[1]}")
	path_of_image = os.path.join(path_of_scaled_images, f"{monster_id}.png")

	# if saved of given size exists, use that
	try:
		image = Image.open(path_of_image, mode="r")

	except FileNotFoundError:
		print("Generating new sized image:", path_of_image)

		# else: create img of that size from original
		path_of_original = os.path.join(path_of_original_images, f"{monster_id}.png")

		image = Image.open(path_of_original, mode="r")
		image.thumbnail(max_size, resample=Image.BICUBIC)

		if not os.path.exists(path_of_scaled_images):
			os.mkdir(path_of_scaled_images)
		image.save(path_of_image, "PNG")

	# format to base64 & return it
	buffer = BytesIO()
	image.save(buffer, format="PNG")
	return base64.b64encode(buffer.getvalue()).decode("utf-8")