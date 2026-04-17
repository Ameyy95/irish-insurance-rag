import argparse

from app.rag.ingest import ingest_folder


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, help="Folder path containing PDFs")
    args = ap.parse_args()

    res = ingest_folder(folder_path=args.folder, actor_role="admin")
    print(f"Ingested: ingest_id={res.ingest_id} files={res.file_count} chunks={res.chunk_count}")


if __name__ == "__main__":
    main()

