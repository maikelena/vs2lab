## Lab3 Wordcount (minimal)

```bash
cd /workspaces/vs2lab/lab3/wordcount

pipenv run python reducer.py 0
pipenv run python reducer.py 1

pipenv run python mapper.py 0
pipenv run python mapper.py 1
pipenv run python mapper.py 2

pipenv run python splitter.py
```

### Expected behavior
- Splitter distributes sentences evenly to the 3 mappers (PUSH/PULL).
- Each mapper splits a sentence into words and sends each word to one of 2 reducers (partition via `len(word) % 2`).
- Each reducer prints the updated count whenever it receives a word.
- After **80** sentences, the whole system terminates automatically.
