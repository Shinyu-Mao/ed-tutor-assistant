import json
import argparse



def anonymise_user(user: dict) -> dict:
    anon = user.copy()

    if "name" in anon:
        parts = anon["name"].split()
        initials = "".join(p[0].upper() for p in parts if p)
        anon["name"] = initials

    if "email" in anon:
        email = anon["email"]
        if "@student" in email:
            anon["email"] = "s@student"
        elif "@edu" in email:
            anon["email"] = "s@edu"

    return anon


def anonymise_comments(comments: list):
    """Recursively anonymise users in nested comments."""
    for comment in comments:
        if "user" in comment and isinstance(comment["user"], dict):
            comment["user"] = anonymise_user(comment["user"])
        anonymise_comments(comment.get("comments", []))


def anonymise_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else [data]

    for entry in entries:
        if "user" in entry and isinstance(entry["user"], dict):
            entry["user"] = anonymise_user(entry["user"])

        for answer in entry.get("answers", []):
            if "user" in answer and isinstance(answer["user"], dict):
                answer["user"] = anonymise_user(answer["user"])
            anonymise_comments(answer.get("comments", []))

        anonymise_comments(entry.get("comments", []))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Anonymised {len(entries)} entries → {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymise name and email in the user field of a JSON file.")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("output", help="Output JSON file")
    args = parser.parse_args()

    anonymise_file(args.input, args.output)
