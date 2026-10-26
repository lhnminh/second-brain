# Visual Second Brain

A daily dashboard to help free up time and mental space. See
[the product spec](visual_second_brain_spec.md) for the current direction.

## Local environment

Create your local configuration if `.env` does not already exist:

```sh
cp -n .env.example .env
```

Keep credentials in `.env`, which Git ignores. The tracked `.env.example`
contains blank placeholders only. Keep it updated when configuration changes.

`META_API_KEY`, `META_BASE_URL`, and `META_MODEL` are planned application settings
for the Meta integration. Confirm the provider's endpoint and model ID when
that integration is implemented. The current Python scaffold does not load
`.env` or use these variables yet.
