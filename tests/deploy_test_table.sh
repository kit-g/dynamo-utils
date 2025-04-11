ENV=dev

if [ -z "${ENV}" ]; then
  PROFILE=default
else
  PROFILE="$ENV"
fi


if sam build -t test_database.yaml ; then
  sam deploy \
   --no-confirm-changeset \
   --config-env "$PROFILE" \
   --profile "$PROFILE"
fi


