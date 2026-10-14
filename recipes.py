"""Offline recipe collection for the SugarBalance SA cookbook."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Recipe:
    name: str
    description: str
    ingredients: tuple[str, ...]
    steps: tuple[str, ...]
    tags: tuple[str, ...]


RECIPES = (
    Recipe(
        name="Chakalaka Bean Bowl",
        description="A filling bowl with beans, vegetables, and brown rice.",
        ingredients=(
            "1 cup cooked brown rice",
            "1 cup no-added-sugar chakalaka",
            "1 cup cooked sugar beans",
            "Fresh coriander (optional)",
        ),
        steps=(
            "Warm the chakalaka and beans together until hot.",
            "Serve over brown rice and finish with coriander.",
        ),
        tags=("lunch", "vegetarian", "fibre"),
    ),
    Recipe(
        name="Spinach and Egg Skillet",
        description="A quick savoury meal with eggs and leafy greens.",
        ingredients=(
            "2 eggs",
            "2 handfuls fresh spinach",
            "1 small tomato, chopped",
            "1 teaspoon cooking oil",
            "Black pepper to taste",
        ),
        steps=(
            "Soften the tomato in oil, then add spinach until wilted.",
            "Add beaten eggs and cook gently until set.",
        ),
        tags=("breakfast", "vegetarian", "quick"),
    ),
    Recipe(
        name="Lentil and Vegetable Pot",
        description="A comforting one-pot meal with lentils and seasonal vegetables.",
        ingredients=(
            "1 cup dried lentils, rinsed",
            "1 onion, chopped",
            "2 carrots, chopped",
            "1 tin chopped tomatoes with no added sugar",
            "3 cups water or low-salt stock",
            "Cumin and black pepper to taste",
        ),
        steps=(
            "Combine ingredients in a pot and bring to a gentle boil.",
            "Simmer until lentils and vegetables are tender, adding water if needed.",
        ),
        tags=("dinner", "vegetarian", "fibre"),
    ),
)


def search_recipes(query: str = "") -> list[Recipe]:
    """Search names, descriptions, ingredients, and tags by all query words."""
    terms = query.casefold().split()
    if not terms:
        return list(RECIPES)

    matches = []
    for recipe in RECIPES:
        searchable_text = " ".join(
            (recipe.name, recipe.description, *recipe.ingredients, *recipe.tags)
        ).casefold()
        if all(term in searchable_text for term in terms):
            matches.append(recipe)
    return matches