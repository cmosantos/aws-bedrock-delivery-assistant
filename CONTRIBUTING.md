# Contribuindo

Contribuições são bem-vindas. Antes de enviar uma alteração, execute a demonstração local, os testes e a validação do template.

```bash
python scripts/local_demo.py
python -m unittest discover -s tests -v
sam validate --lint
```

Mantenha as regras financeiras fora do modelo generativo. Novos itens devem ser adicionados ao cardápio oficial e os cálculos precisam continuar sendo realizados no backend.
