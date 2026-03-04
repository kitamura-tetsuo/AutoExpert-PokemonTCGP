uv sync
source .venv/bin/activate
cd deckgym-core
uvx maturin develop --features python
cd ..
python main.py vs-past \
    --matches 100 \
    --threshold 0 \
    --league-student train_data/all.csv \
    --league-teacher train_data/all.csv
