"""Extract book titles and authors from raw social media post text."""
import re
from collections import defaultdict


# Well-known BookTok books for fuzzy matching
KNOWN_BOOKS = {
    "a court of thorns and roses": ("A Court of Thorns and Roses", "Sarah J. Maas"),
    "acotar": ("A Court of Thorns and Roses", "Sarah J. Maas"),
    "a court of mist and fury": ("A Court of Mist and Fury", "Sarah J. Maas"),
    "a court of wings and ruin": ("A Court of Wings and Ruin", "Sarah J. Maas"),
    "fourth wing": ("Fourth Wing", "Rebecca Yarros"),
    "iron flame": ("Iron Flame", "Rebecca Yarros"),
    "onyx storm": ("Onyx Storm", "Rebecca Yarros"),
    "haunting adeline": ("Haunting Adeline", "H.D. Carlton"),
    "hunting adeline": ("Hunting Adeline", "H.D. Carlton"),
    "it ends with us": ("It Ends with Us", "Colleen Hoover"),
    "it starts with us": ("It Starts with Us", "Colleen Hoover"),
    "ugly love": ("Ugly Love", "Colleen Hoover"),
    "verity": ("Verity", "Colleen Hoover"),
    "november 9": ("November 9", "Colleen Hoover"),
    "reminders of him": ("Reminders of Him", "Colleen Hoover"),
    "confess": ("Confess", "Colleen Hoover"),
    "twisted love": ("Twisted Love", "Ana Huang"),
    "twisted games": ("Twisted Games", "Ana Huang"),
    "twisted hate": ("Twisted Hate", "Ana Huang"),
    "twisted lies": ("Twisted Lies", "Ana Huang"),
    "king of wrath": ("King of Wrath", "Ana Huang"),
    "king of pride": ("King of Pride", "Ana Huang"),
    "king of greed": ("King of Greed", "Ana Huang"),
    "king of sloth": ("King of Sloth", "Ana Huang"),
    "the love hypothesis": ("The Love Hypothesis", "Ali Hazelwood"),
    "love on the brain": ("Love on the Brain", "Ali Hazelwood"),
    "check & mate": ("Check & Mate", "Ali Hazelwood"),
    "bride": ("Bride", "Ali Hazelwood"),
    "butcher and blackbird": ("Butcher & Blackbird", "Brynne Weaver"),
    "butcher & blackbird": ("Butcher & Blackbird", "Brynne Weaver"),
    "the song of achilles": ("The Song of Achilles", "Madeline Miller"),
    "song of achilles": ("The Song of Achilles", "Madeline Miller"),
    "circe": ("Circe", "Madeline Miller"),
    "the seven husbands of evelyn hugo": ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid"),
    "seven husbands of evelyn hugo": ("The Seven Husbands of Evelyn Hugo", "Taylor Jenkins Reid"),
    "daisy jones and the six": ("Daisy Jones & The Six", "Taylor Jenkins Reid"),
    "malibu rising": ("Malibu Rising", "Taylor Jenkins Reid"),
    "the cruel prince": ("The Cruel Prince", "Holly Black"),
    "the wicked king": ("The Wicked King", "Holly Black"),
    "the queen of nothing": ("The Queen of Nothing", "Holly Black"),
    "shatter me": ("Shatter Me", "Tahereh Mafi"),
    "powerless": ("Powerless", "Lauren Roberts"),
    "reckless": ("Reckless", "Lauren Roberts"),
    "fearless": ("Fearless", "Lauren Roberts"),
    "community": ("Community", "Lauren Roberts"),
    "project hail mary": ("Project Hail Mary", "Andy Weir"),
    "the name of the wind": ("The Name of the Wind", "Patrick Rothfuss"),
    "the priory of the orange tree": ("The Priory of the Orange Tree", "Samantha Shannon"),
    "throne of glass": ("Throne of Glass", "Sarah J. Maas"),
    "house of earth and blood": ("House of Earth and Blood", "Sarah J. Maas"),
    "crescent city": ("Crescent City", "Sarah J. Maas"),
    "still beating": ("Still Beating", "Jennifer Hartmann"),
    "punk 57": ("Punk 57", "Penelope Douglas"),
    "credence": ("Credence", "Penelope Douglas"),
    "birthday girl": ("Birthday Girl", "Penelope Douglas"),
    "god of malice": ("God of Malice", "Rina Kent"),
    "god of pain": ("God of Pain", "Rina Kent"),
    "god of wrath": ("God of Wrath", "Rina Kent"),
    "god of ruin": ("God of Ruin", "Rina Kent"),
    "pucking wrong": ("Pucking Wrong", "C.R. Jane & Mila Young"),
    "lights out": ("Lights Out", "Navessa Allen"),
    "nocticadia": ("Nocticadia", "Keri Lake"),
    "brutal prince": ("Brutal Prince", "Sophie Lark"),
    "brutal intentions": ("Brutal Intentions", "B. Celeste"),
    "little stranger": ("Her Soul to Take", "Harley Laroux"),
    "her soul to take": ("Her Soul to Take", "Harley Laroux"),
    "the sword of kaigen": ("The Sword of Kaigen", "M.L. Wang"),
    "the hero of ages": ("The Hero of Ages", "Brandon Sanderson"),
    "the will of the many": ("The Will of the Many", "James Islington"),
    "words of radiance": ("Words of Radiance", "Brandon Sanderson"),
    "the way of kings": ("The Way of Kings", "Brandon Sanderson"),
    "lies of locke lamora": ("The Lies of Locke Lamora", "Scott Lynch"),
    "pillars of the earth": ("The Pillars of the Earth", "Ken Follett"),
    "lonesome dove": ("Lonesome Dove", "Larry McMurtry"),
    "run posy run": ("Run Posy Run", "Cate C. Wells"),
    "the sweetest oblivion": ("The Sweetest Oblivion", "Danielle Lori"),
    "my dark romeo": ("My Dark Romeo", "Parker S. Huntington & L.J. Shen"),
    "my dark prince": ("My Dark Prince", "Parker S. Huntington & L.J. Shen"),
    "crave": ("Crave", "Luna Mason"),
    "false play": ("False Play", "Yinn Quirós"),
    "meet me at the metro": ("Meet Me at the Metro", "Savanna Jade"),
    "white nights": ("White Nights", "Fyodor Dostoevsky"),
    "bunny": ("Bunny", "Mona Awad"),
    "the secret history": ("The Secret History", "Donna Tartt"),
    "normal people": ("Normal People", "Sally Rooney"),
    "beach read": ("Beach Read", "Emily Henry"),
    "people we meet on vacation": ("People We Meet on Vacation", "Emily Henry"),
    "book lovers": ("Book Lovers", "Emily Henry"),
    "happy place": ("Happy Place", "Emily Henry"),
    "funny story": ("Funny Story", "Emily Henry"),
    "the atlas six": ("The Atlas Six", "Olivie Blake"),
    "divine rivals": ("Divine Rivals", "Rebecca Ross"),
    "assistant to the villain": ("Assistant to the Villain", "Hannah Nicole Maehrer"),
}


def extract_books_from_text(text):
    """Extract book mentions from a post's text."""
    if not text:
        return []

    found = []
    text_lower = text.lower()

    # Match against known books
    for key, (title, author) in KNOWN_BOOKS.items():
        if key in text_lower:
            found.append((title, author))

    # Pattern: "Title by Author" — capture title + author
    by_pattern = re.findall(
        r'📚[:\s]*([A-Z][A-Za-z\s\'\-&]+?)\s+by\s+([A-Z][A-Za-z\s\.\-&]+?)(?:\s{2,}|\n|#|$)',
        text,
    )
    for title, author in by_pattern:
        title = title.strip().rstrip(" -")
        author = author.strip().rstrip(" -")
        if len(title) > 3 and len(author) > 3:
            normalized = title.lower()
            if normalized not in KNOWN_BOOKS:
                found.append((title, author))

    # Deduplicate by title
    seen = set()
    unique = []
    for title, author in found:
        key = title.lower()
        if key not in seen:
            seen.add(key)
            unique.append((title, author))

    return unique


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
        "sample_urls": [],
    })

    for post in posts:
        books = extract_books_from_text(post.get("text", "") if isinstance(post, dict) else post.text)
        for title, author in books:
            key = title.lower()
            stats = book_stats[key]
            stats["title"] = title
            stats["author"] = author
            stats["mentions"] += 1

            if isinstance(post, dict):
                stats["total_views"] += post.get("view_count", 0) or 0
                stats["total_likes"] += post.get("like_count", 0) or 0
                stats["total_comments"] += post.get("comment_count", 0) or 0
                stats["platforms"].add(post.get("platform", ""))
                if post.get("url") and len(stats["sample_urls"]) < 3:
                    stats["sample_urls"].append(post["url"])
            else:
                stats["total_views"] += post.view_count or 0
                stats["total_likes"] += post.like_count or 0
                stats["total_comments"] += post.comment_count or 0
                stats["platforms"].add(post.platform or "")
                if post.url and len(stats["sample_urls"]) < 3:
                    stats["sample_urls"].append(post.url)

    # Score: weighted combination of mentions, views, likes
    ranked = []
    for key, stats in book_stats.items():
        score = (
            stats["mentions"] * 1000
            + stats["total_views"] * 0.001
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
            "sample_urls": stats["sample_urls"],
            "score": round(score, 2),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]
