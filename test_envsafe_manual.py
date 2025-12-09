from envsafe import env, EnvError

def main():
    try:
        debug = env.bool("DEBUG", default=False)
        port = env.int("PORT", default=8000, min=1, max=65535)
        db_url = env.url("DATABASE_URL", required=False)
        mode = env.choice("MODE", choices=["dev", "prod"], default="dev")
        hosts = env.list("ALLOWED_HOSTS", default=["localhost"])

        print("DEBUG:", debug)
        print("PORT:", port)
        print("DATABASE_URL:", db_url)
        print("MODE:", mode)
        print("ALLOWED_HOSTS:", hosts)

    except EnvError as e:
        print("Configuration error:", e)


if __name__ == "__main__":
    main()
