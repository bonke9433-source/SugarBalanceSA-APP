import unittest

from recipes import RECIPES, search_recipes


class RecipeSearchTests(unittest.TestCase):
    def test_empty_query_returns_all_recipes(self) -> None:
        self.assertEqual(search_recipes(), list(RECIPES))
        self.assertEqual(search_recipes("   "), list(RECIPES))

    def test_search_is_case_insensitive_and_matches_all_words(self) -> None:
        results = search_recipes("RICE brown")

        self.assertEqual([recipe.name for recipe in results], ["Chakalaka Bean Bowl"])

    def test_search_matches_ingredients_and_tags(self) -> None:
        self.assertEqual(
            [recipe.name for recipe in search_recipes("spinach")],
            ["Spinach and Egg Skillet"],
        )
        self.assertEqual(
            [recipe.name for recipe in search_recipes("quick breakfast")],
            ["Spinach and Egg Skillet"],
        )

    def test_non_matching_query_returns_no_recipes(self) -> None:
        self.assertEqual(search_recipes("chocolate cake"), [])


if __name__ == "__main__":
    unittest.main()
