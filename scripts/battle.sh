uv sync
source .venv/bin/activate
cd deckgym-core
uvx maturin develop --features python
cd ..
python main.py show-battle --deck-a train_data/cacc7f16.txt --deck-b train_data/20d1a998.txt
