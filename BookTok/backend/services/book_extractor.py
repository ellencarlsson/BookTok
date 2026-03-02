"""Extract trending books from raw posts using text matching."""
import re
from collections import defaultdict


KNOWN_BOOKS = {
    # Sarah J. Maas
    "a court of thorns and roses": ("A Court of Thorns and Roses", "Sarah J. Maas"),
    "acotar": ("A Court of Thorns and Roses", "Sarah J. Maas"),
    "a court of mist and fury": ("A Court of Mist and Fury", "Sarah J. Maas"),
    "acomaf": ("A Court of Mist and Fury", "Sarah J. Maas"),
    "a court of wings and ruin": ("A Court of Wings and Ruin", "Sarah J. Maas"),
    "acowar": ("A Court of Wings and Ruin", "Sarah J. Maas"),
    "a court of frost and starlight": ("A Court of Frost and Starlight", "Sarah J. Maas"),
    "acofas": ("A Court of Frost and Starlight", "Sarah J. Maas"),
    "a court of silver flames": ("A Court of Silver Flames", "Sarah J. Maas"),
    "acosf": ("A Court of Silver Flames", "Sarah J. Maas"),
    "throne of glass": ("Throne of Glass", "Sarah J. Maas"),
    "tog": ("Throne of Glass", "Sarah J. Maas"),
    "house of earth and blood": ("House of Earth and Blood", "Sarah J. Maas"),
    "crescent city": ("Crescent City", "Sarah J. Maas"),
    "cc": ("Crescent City", "Sarah J. Maas"),
    # Rebecca Yarros
    "fourth wing": ("Fourth Wing", "Rebecca Yarros"),
    "fw": ("Fourth Wing", "Rebecca Yarros"),
    "iron flame": ("Iron Flame", "Rebecca Yarros"),
    "onyx storm": ("Onyx Storm", "Rebecca Yarros"),
    # Colleen Hoover
    "it ends with us": ("It Ends with Us", "Colleen Hoover"),
    "iewu": ("It Ends with Us", "Colleen Hoover"),
    "it starts with us": ("It Starts with Us", "Colleen Hoover"),
    "ugly love": ("Ugly Love", "Colleen Hoover"),
    "verity": ("Verity", "Colleen Hoover"),
    "november 9": ("November 9", "Colleen Hoover"),
    "reminders of him": ("Reminders of Him", "Colleen Hoover"),
    "confess": ("Confess", "Colleen Hoover"),
    "coho": ("Colleen Hoover", "Colleen Hoover"),
    # Ana Huang
    "twisted love": ("Twisted Love", "Ana Huang"),
    "twisted games": ("Twisted Games", "Ana Huang"),
    "twisted hate": ("Twisted Hate", "Ana Huang"),
    "twisted lies": ("Twisted Lies", "Ana Huang"),
    "king of wrath": ("King of Wrath", "Ana Huang"),
    "king of pride": ("King of Pride", "Ana Huang"),
    "king of greed": ("King of Greed", "Ana Huang"),
    "king of sloth": ("King of Sloth", "Ana Huang"),
    # Ali Hazelwood
    "the love hypothesis": ("The Love Hypothesis", "Ali Hazelwood"),
    "love on the brain": ("Love on the Brain", "Ali Hazelwood"),
    "check & mate": ("Check & Mate", "Ali Hazelwood"),
    "bride": ("Bride", "Ali Hazelwood"),
    # H.D. Carlton
    "haunting adeline": ("Haunting Adeline", "H.D. Carlton"),
    "hunting adeline": ("Hunting Adeline", "H.D. Carlton"),
    # Penelope Douglas
    "punk 57": ("Punk 57", "Penelope Douglas"),
    "credence": ("Credence", "Penelope Douglas"),
    "birthday girl": ("Birthday Girl", "Penelope Douglas"),
    "bully": ("Bully", "Penelope Douglas"),
    # Emily Henry
    "beach read": ("Beach Read", "Emily Henry"),
    "people we meet on vacation": ("People We Meet on Vacation", "Emily Henry"),
    "book lovers": ("Book Lovers", "Emily Henry"),
    "happy place": ("Happy Place", "Emily Henry"),
    "funny story": ("Funny Story", "Emily Henry"),
    # Madeline Miller
    "the song of achilles": ("The Song of Achilles", "Madeline Miller"),
    "song of achilles": ("The Song of Achilles", "Madeline Miller"),
    "tsoa": ("The Song of Achilles", "Madeline Miller"),
    "circe": ("Circe", "Madeline Miller"),
    # Taylor Jenkins Reid
    "the seven husbands of evelyn hugo": ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid"),
    "seven husbands of evelyn hugo": ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid"),
    "evelyn hugo": ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid"),
    "daisy jones and the six": ("Daisy Jones & The Six", "Taylor Jenkins Reid"),
    "malibu rising": ("Malibu Rising", "Taylor Jenkins Reid"),
    # Lauren Roberts
    "powerless": ("Powerless", "Lauren Roberts"),
    "reckless": ("Reckless", "Lauren Roberts"),
    "fearless": ("Fearless", "Lauren Roberts"),
    # Holly Black
    "the cruel prince": ("The Cruel Prince", "Holly Black"),
    "the wicked king": ("The Wicked King", "Holly Black"),
    "the queen of nothing": ("The Queen of Nothing", "Holly Black"),
    # Brynne Weaver
    "butcher and blackbird": ("Butcher & Blackbird", "Brynne Weaver"),
    "butcher & blackbird": ("Butcher & Blackbird", "Brynne Weaver"),
    # Jennifer L. Armentrout
    "from blood and ash": ("From Blood and Ash", "Jennifer L. Armentrout"),
    "fbaa": ("From Blood and Ash", "Jennifer L. Armentrout"),
    "a kingdom of flesh and fire": ("A Kingdom of Flesh and Fire", "Jennifer L. Armentrout"),
    # Rina Kent
    "god of malice": ("God of Malice", "Rina Kent"),
    "god of pain": ("God of Pain", "Rina Kent"),
    "god of wrath": ("God of Wrath", "Rina Kent"),
    "god of ruin": ("God of Ruin", "Rina Kent"),
    # Rebecca Ross
    "divine rivals": ("Divine Rivals", "Rebecca Ross"),
    "ruthless vows": ("Ruthless Vows", "Rebecca Ross"),
    # Misc popular
    "the secret history": ("The Secret History", "Donna Tartt"),
    "normal people": ("Normal People", "Sally Rooney"),
    "the atlas six": ("The Atlas Six", "Olivie Blake"),
    "assistant to the villain": ("Assistant to the Villain", "Hannah Nicole Maehrer"),
    "shatter me": ("Shatter Me", "Tahereh Mafi"),
    "the invisible life of addie larue": ("The Invisible Life of Addie LaRue", "V.E. Schwab"),
    "addie larue": ("The Invisible Life of Addie LaRue", "V.E. Schwab"),
    "project hail mary": ("Project Hail Mary", "Andy Weir"),
    "the name of the wind": ("The Name of the Wind", "Patrick Rothfuss"),
    "still beating": ("Still Beating", "Jennifer Hartmann"),
    "run posy run": ("Run Posy Run", "Cate C. Wells"),
    "the sweetest oblivion": ("The Sweetest Oblivion", "Danielle Lori"),
    "lights out": ("Lights Out", "Navessa Allen"),
    "brutal prince": ("Brutal Prince", "Sophie Lark"),
    "her soul to take": ("Her Soul to Take", "Harley Laroux"),
    "false play": ("False Play", "Yinn Quirós"),
    "bunny": ("Bunny", "Mona Awad"),
    "the way of kings": ("The Way of Kings", "Brandon Sanderson"),
    "words of radiance": ("Words of Radiance", "Brandon Sanderson"),
    "the priory of the orange tree": ("The Priory of the Orange Tree", "Samantha Shannon"),
    "house of salt and sorrows": ("House of Salt and Sorrows", "Erin A. Craig"),
    "kingdom of the wicked": ("Kingdom of the Wicked", "Kerri Maniscalco"),
    "kotw": ("Kingdom of the Wicked", "Kerri Maniscalco"),
    "the spanish love deception": ("The Spanish Love Deception", "Elena Armas"),
    "the deal": ("The Deal", "Elle Kennedy"),
    "icebreaker": ("Icebreaker", "Hannah Grace"),
    "wildfire": ("Wildfire", "Hannah Grace"),
    "the fine print": ("The Fine Print", "Lauren Asher"),
    "terms and conditions": ("Terms and Conditions", "Lauren Asher"),
    "things we never got over": ("Things We Never Got Over", "Lucy Score"),
    "things we hide from the light": ("Things We Hide from the Light", "Lucy Score"),
    "the hating game": ("The Hating Game", "Sally Thorne"),
    "the unhoneymooners": ("The Unhoneymooners", "Christina Lauren"),
    "the kiss quotient": ("The Kiss Quotient", "Helen Hoang"),
    "red white and royal blue": ("Red, White & Royal Blue", "Casey McQuiston"),
    "rwrb": ("Red, White & Royal Blue", "Casey McQuiston"),
    "the midnight library": ("The Midnight Library", "Matt Haig"),
    "the house in the cerulean sea": ("The House in the Cerulean Sea", "TJ Klune"),
    "heartstopper": ("Heartstopper", "Alice Oseman"),
    "six of crows": ("Six of Crows", "Leigh Bardugo"),
    "shadow and bone": ("Shadow and Bone", "Leigh Bardugo"),
    "the poppy war": ("The Poppy War", "R.F. Kuang"),
    "babel": ("Babel", "R.F. Kuang"),
    "yellowface": ("Yellowface", "R.F. Kuang"),
    "my dark romeo": ("My Dark Romeo", "Parker S. Huntington"),
    "crave": ("Crave", "Tracy Wolff"),
    "caraval": ("Caraval", "Stephanie Garber"),
    "once upon a broken heart": ("Once Upon a Broken Heart", "Stephanie Garber"),
    "the inheritance games": ("The Inheritance Games", "Jennifer Lynn Barnes"),
    "a good girl's guide to murder": ("A Good Girl's Guide to Murder", "Holly Jackson"),
    "we have always lived in the castle": ("We Have Always Lived in the Castle", "Shirley Jackson"),
    "the silent patient": ("The Silent Patient", "Alex Michaelides"),
    "where the crawdads sing": ("Where the Crawdads Sing", "Delia Owens"),
    "the nightingale": ("The Nightingale", "Kristin Hannah"),
    "the great alone": ("The Great Alone", "Kristin Hannah"),
    "say nothing": ("Say Nothing", "Patrick Radden Keefe"),
    # Scarlett St. Clair
    "a touch of darkness": ("A Touch of Darkness", "Scarlett St. Clair"),
    "a touch of chaos": ("A Touch of Chaos", "Scarlett St. Clair"),
    # Mariana Zapata
    "from lukov with love": ("From Lukov with Love", "Mariana Zapata"),
    "when gracie met the grump": ("When Gracie Met the Grump", "Mariana Zapata"),
    # Michelle Naomi Mosley
    "rare blend": ("Rare Blend", "Michelle Naomi Mosley"),
    "double barrel": ("Double Barrel", "Michelle Naomi Mosley"),
    "bottle shock": ("Bottle Shock", "Michelle Naomi Mosley"),
    # Misc BookTok popular
    "beneath": ("Beneath", "Ariel Sullivan"),
    "lovestruck": ("Lovestruck", "Ivy Dawes"),
    "luxuria": ("Luxuria", "Colette Rhodes"),
    "sweet venom": ("Sweet Venom", "Rina Kent"),
    "rewind it back": ("Rewind It Back", "Liz Tomforde"),
    "clutch and shift": ("Clutch and Shift", "Brittany Ann"),
    "never lie": ("Never Lie", "Freida McFadden"),
    "the wedding people": ("The Wedding People", "Alison Espach"),
    "the selection": ("The Selection", "Kiera Cass"),
    "love song": ("Love Song", "Elle Kennedy"),
    "wildest dreams": ("Wildest Dreams", "LJ Shen"),
    "rival darling": ("Rival Darling", "Alexandra Moody"),
    "starside": ("Starside", "Alex Aster"),
    "boys of brayshaw": ("Boys of Brayshaw", "Meagan Brandy"),
    "his pretty little burden": ("His Pretty Little Burden", "Nicci Harris"),
    "ruthless titan": ("Ruthless Titan", "E.V. Olsen"),
    "scars of you": ("Scars of You", "Madi Danielle"),
    "instinct": ("Instinct", "Luna Mason"),
    "almost rotten": ("Almost Rotten", "Abby Millsaps"),
    "too safe": ("Too Safe", "Abby Millsaps"),
    "whisper sweet nothings": ("Whisper Sweet Nothings", "Laura Pavlov"),
    "within range": ("Within Range", "Ruth Stilling"),
    "storms of secrets and sorrow": ("Storms of Secrets and Sorrow", "Melissa K. Roehrich"),
    "otherworldly": ("Otherworldly", "F.T. Lukens"),
    # Dark/spicy romance
    "the mindf series": ("The MindF Series", "S.T. Abby"),
    "midnight message": ("Midnight Message", "Avina St. Graves"),
    "her soul to take": ("Her Soul to Take", "Harley Laroux"),
    # Classics & literary
    "pride and prejudice": ("Pride and Prejudice", "Jane Austen"),
    "dracula": ("Dracula", "Bram Stoker"),
    "gone girl": ("Gone Girl", "Gillian Flynn"),
    "ready player one": ("Ready Player One", "Ernest Cline"),
    "bury my heart at wounded knee": ("Bury My Heart at Wounded Knee", "Dee Brown"),
    "the spear cuts through water": ("The Spear Cuts Through Water", "Simon Jimenez"),
    "dragonfly in amber": ("Dragonfly in Amber", "Diana Gabaldon"),
    "the bright years": ("The Bright Years", "Sarah Damoff"),
    "the deep": ("The Deep", "Rivers Solomon"),
    "razorblade tears": ("Razorblade Tears", "S.A. Crosby"),
    "devolution": ("Devolution", "Max Brooks"),
    "the weight of blood": ("The Weight of Blood", "Tiffany D. Jackson"),
    "good spirits": ("Good Spirits", "B.K. Borison"),
    "we'll prescribe you a cat": ("We'll Prescribe You a Cat", "Syou Ishida"),
    "playground": ("Playground", "Aron Beauregard"),
}

# Short abbreviations that need word boundary matching to avoid false positives
SHORT_ABBREVIATIONS = {
    "fw", "cc", "tog", "iewu", "tsoa", "fbaa", "acosf", "acomaf",
    "acowar", "acofas", "kotw", "rwrb", "coho",
}


def extract_books_from_text(text):
    """Extract book mentions from post text."""
    if not text:
        return []

    found = []
    text_lower = text.lower()
    seen = set()

    for key, (title, author) in KNOWN_BOOKS.items():
        if title.lower() in seen:
            continue

        if key in SHORT_ABBREVIATIONS:
            if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
                seen.add(title.lower())
                found.append({"title": title, "author": author})
        else:
            if key in text_lower:
                seen.add(title.lower())
                found.append({"title": title, "author": author})

    # Pattern: "Title by Author" — stop at dash, comma, newline, or hashtag
    by_matches = re.findall(
        r'["\']?([A-Z][A-Za-z\s\'\-&:]+?)["\']?\s+by\s+([A-Z][A-Za-z\s.]+?)(?:\s*[-,#\n]|$)',
        text,
    )
    for title, author in by_matches:
        title = title.strip().rstrip(" -")
        author = author.strip().rstrip(" -")
        if (
            len(title) > 3
            and len(title) <= 60
            and len(title.split()) <= 6
            and len(author) > 3
            and title.lower() not in seen
        ):
            seen.add(title.lower())
            found.append({"title": title, "author": author})

    return found


def extract_trending_books(posts, limit=15):
    """Analyze posts and return top trending books."""
    book_stats = defaultdict(lambda: {
        "title": "",
        "author": "",
        "mentions": 0,
        "total_views": 0,
        "total_likes": 0,
        "total_comments": 0,
        "platforms": set(),
    })

    for post in posts:
        text = post.get("text", "") if isinstance(post, dict) else (post.text or "")
        books = extract_books_from_text(text)

        for book in books:
            title = book["title"]
            key = title.lower()
            stats = book_stats[key]
            stats["title"] = title
            stats["author"] = book["author"]
            stats["mentions"] += 1

            if isinstance(post, dict):
                stats["total_views"] += post.get("view_count", 0) or 0
                stats["total_likes"] += post.get("like_count", 0) or 0
                stats["total_comments"] += post.get("comment_count", 0) or 0
                stats["platforms"].add(post.get("platform", ""))
            else:
                stats["total_views"] += post.view_count or 0
                stats["total_likes"] += post.like_count or 0
                stats["total_comments"] += post.comment_count or 0
                stats["platforms"].add(post.platform or "")

    ranked = []
    for stats in book_stats.values():
        score = (
            stats["mentions"] * 1000
            + stats["total_likes"] * 0.1
            + stats["total_comments"] * 0.5
        )
        ranked.append({
            "title": stats["title"],
            "author": stats["author"],
            "mentions": stats["mentions"],
            "total_views": stats["total_views"],
            "total_likes": stats["total_likes"],
            "total_comments": stats["total_comments"],
            "platforms": sorted(stats["platforms"]),
            "score": round(score, 2),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]
