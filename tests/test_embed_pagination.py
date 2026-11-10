import unittest

import discord

from main import paginated_embeds


class EmbedPaginationTests(unittest.TestCase):
    def test_long_description_is_split_without_losing_text(self):
        source = "x" * 5000
        embed = discord.Embed(title="Long response", description=source)
        pages = paginated_embeds(embed)
        self.assertGreater(len(pages), 1)
        self.assertEqual("".join(page.description or "" for page in pages), source)
        self.assertTrue(all(len(page.description or "") <= 4096 for page in pages))

    def test_long_field_is_split_into_continuation_fields(self):
        source = "field-content " * 300
        embed = discord.Embed(title="Long field")
        embed.add_field(name="Details", value=source)
        pages = paginated_embeds(embed)
        values = [field.value for page in pages for field in page.fields]
        self.assertEqual("".join(values), source)
        self.assertGreater(len(values), 1)
        self.assertTrue(all(len(value) <= 1024 for value in values))

    def test_more_than_twenty_five_fields_are_paginated(self):
        embed = discord.Embed(title="Many fields")
        for index in range(30):
            embed.add_field(name=f"Field {index}", value=f"Value {index}")
        pages = paginated_embeds(embed)
        self.assertEqual(sum(len(page.fields) for page in pages), 30)
        self.assertTrue(all(len(page.fields) <= 25 for page in pages))


if __name__ == "__main__":
    unittest.main()
