# Call from the root folder

source venv/bin/activate

python -m grpc_tools.protoc \
  -I ./proto \
  --python_out=./app/gen \
  --grpc_python_out=./app/gen \
  ./proto/*.proto
