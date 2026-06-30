# Arquitetura da solução

## Objetivo

A solução demonstra como combinar orquestração serverless e inteligência artificial generativa em um atendimento de delivery. O AWS Step Functions atua como o coordenador central, enquanto o Amazon Bedrock interpreta a linguagem natural sem assumir responsabilidades críticas da aplicação.

## Componentes

### Amazon API Gateway

Expõe a rota `POST /assistant`. A API recebe mensagens em JSON e encaminha a execução para a função de entrada.

### Request Handler

A função converte o corpo HTTP em um objeto, adiciona metadados básicos e chama `StartSyncExecution` em uma máquina de estados Express. A resposta do workflow é convertida para o formato esperado pelo API Gateway.

### AWS Step Functions Express

O modo Express foi escolhido porque o atendimento é curto, possui alto potencial de volume e precisa responder de forma síncrona. O workflow controla a ordem das tarefas, as retentativas e os caminhos de erro.

### Validação

A primeira função impede mensagens vazias ou excessivamente longas, normaliza o usuário e cria um identificador de sessão quando necessário.

### Cardápio

O exemplo mantém um cardápio estático em uma função para facilitar a implantação. Em produção, o conteúdo poderia ser armazenado no DynamoDB, AppConfig ou outro serviço gerenciado.

### Amazon Bedrock

A função de interpretação usa a API Converse. O prompt exige uma resposta JSON com intenção, mensagem, itens, quantidades e código do pedido. A temperatura baixa reduz variações desnecessárias.

### Regra de negócio

A função de criação compara os IDs retornados pelo modelo com o cardápio oficial. Quantidades são limitadas e preços são calculados no backend. Essa separação evita confiar no modelo para operações financeiras.

### DynamoDB

Os pedidos são armazenados com chave primária `order_id`. A tabela utiliza capacidade sob demanda, criptografia, recuperação point-in-time e TTL.

## Contrato de entrada

```json
{
  "user_id": "cliente-123",
  "session_id": "opcional",
  "locale": "pt-BR",
  "message": "Quero uma pizza de calabresa"
}
```

## Contrato de saída

```json
{
  "intent": "CREATE_ORDER",
  "reply": "Pedido PED-XXXXXXXX recebido com sucesso.",
  "order": {
    "order_id": "PED-XXXXXXXX",
    "status": "RECEIVED"
  }
}
```

## Decisões técnicas

A integração do Bedrock foi encapsulada em Lambda para aproveitar a API Converse e permitir a troca de modelos sem alterar a máquina de estados. O Step Functions continua responsável por toda a orquestração. Uma evolução possível seria utilizar a integração otimizada `bedrock:invokeModel` diretamente em um estado Task quando o formato específico do modelo estiver definido.

A aplicação evita armazenar o histórico completo da conversa. Para suporte a contexto de múltiplos turnos, uma tabela adicional por sessão ou um mecanismo de memória controlada poderia ser incluído.
