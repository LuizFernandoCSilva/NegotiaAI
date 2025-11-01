import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.infrastructure.database.seed import run_seed, check_data


def main():    
    try:
        run_seed()
        check_data()
        
    except Exception as e:
        print(f"\n Erro ao executar seed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()