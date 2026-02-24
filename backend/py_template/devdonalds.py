from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here! (name -> entry dict)
cookbook: Dict[str, Union[Recipe, Ingredient]] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str):
	# Replace hyphens and underscores with spaces
	s = recipeName.replace('-', ' ').replace('_', ' ')
	# Keep only letters and spaces
	s = ''.join(c for c in s if c.isalpha() or c.isspace())
	# Collapse multiple spaces, trim
	s = ' '.join(s.split())
	# Capitalise each word
	s = ' '.join(word.capitalize() for word in s.split())

	if len(s) == 0: # None if empty
		return None
	return s


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	if data is None:
		return '', 400

	entry_type = data.get('type')
	name = data.get('name')

	if entry_type not in ('recipe', 'ingredient'):
		return '', 400

	# Normalise name for uniqueness check (case-sensitive per test: "Beef" != "beef")
	if name in cookbook:
		return '', 400

	if entry_type == 'ingredient':
		cook_time = data.get('cookTime')
		if cook_time is None or not isinstance(cook_time, int) or cook_time < 0:
			return '', 400
		cookbook[name] = Ingredient(name=name, cook_time=cook_time)
	else:
		required_items_raw = data.get('requiredItems')
		if required_items_raw is None or not isinstance(required_items_raw, list):
			return '', 400
		seen_names = set()
		required_items = []
		for item in required_items_raw:
			item_name = item.get('name')
			quantity = item.get('quantity')
			if item_name is None or quantity is None or not isinstance(quantity, int) or quantity < 0:
				return '', 400
			if item_name in seen_names:
				return '', 400
			seen_names.add(item_name)
			required_items.append(RequiredItem(name=item_name, quantity=quantity))
		cookbook[name] = Recipe(name=name, required_items=required_items)

	return jsonify({}), 200


def _flatten_ingredients(entry_name: str, quantity: int) -> List[RequiredItem]:
	"""Recursively flatten a recipe/ingredient into base ingredients with quantities."""
	entry = cookbook.get(entry_name)
	if entry is None:
		raise ValueError(f"Entry '{entry_name}' not found")
	if isinstance(entry, Ingredient):
		return [RequiredItem(name=entry_name, quantity=quantity)]
	# It's a Recipe
	result = []
	for item in entry.required_items:
		result.extend(_flatten_ingredients(item.name, item.quantity * quantity))
	return result

def _merge_ingredients(items: List[RequiredItem]) -> List[RequiredItem]:
	"""Merge duplicate ingredients by summing quantities."""
	merged: Dict[str, int] = {}
	for item in items:
		merged[item.name] = merged.get(item.name, 0) + item.quantity
	return [RequiredItem(name=name, quantity=qty) for name, qty in merged.items()]

def _compute_cook_time(ingredients: List[RequiredItem]) -> int:
	"""Sum cookTime * quantity for each base ingredient."""
	total = 0
	for item in ingredients:
		entry = cookbook.get(item.name)
		if entry is None or not isinstance(entry, Ingredient):
			raise ValueError(f"Ingredient '{item.name}' not found")
		total += entry.cook_time * item.quantity
	return total

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get('name')
	if not name:
		return '', 400
	entry = cookbook.get(name)
	if entry is None:
		return '', 400
	if isinstance(entry, Ingredient):
		return '', 400
	try:
		flat = []
		for item in entry.required_items:
			flat.extend(_flatten_ingredients(item.name, item.quantity))
		ingredients = _merge_ingredients(flat)
		cook_time = _compute_cook_time(ingredients)
	except ValueError:
		return '', 400
	return jsonify({
		'name': entry.name,
		'cookTime': cook_time,
		'ingredients': [{'name': i.name, 'quantity': i.quantity} for i in ingredients]
	}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
