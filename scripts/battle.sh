source .venv/bin/activate
cd deckgym-core
uv sync
uvx maturin develop --features python
cd ..
python main.py show-battle --deck-a train_data/4f151f7b.txt --deck-b train_data/20d1a998.txt
