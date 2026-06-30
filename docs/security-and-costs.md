# Segurança, custos e evolução para produção

## Segurança

O projeto usa permissões separadas por função. Mesmo assim, uma implantação pública de produção deve adicionar autenticação, autorização e limitação de tráfego.

Recomendações:

1. Proteger a API com Amazon Cognito, JWT Authorizer ou outro provedor de identidade.
2. Configurar throttling e cotas no API Gateway.
3. Restringir CORS aos domínios autorizados.
4. Usar AWS WAF para reduzir abuso e tráfego malicioso.
5. Armazenar dados pessoais somente quando realmente necessários.
6. Aplicar Amazon Bedrock Guardrails para políticas de conteúdo.
7. Criar alarmes no CloudWatch para erros, latência e volume inesperado.
8. Configurar AWS Budgets e alertas de custo.
9. Validar ownership do pedido com identidade autenticada, não apenas com `user_id` enviado pelo cliente.
10. Revisar retenção de logs e dados conforme requisitos legais.

## Controle de alucinações

O modelo recebe o cardápio como contexto e deve usar somente IDs existentes. A função de criação rejeita qualquer ID desconhecido e recalcula todos os valores. Essa estratégia mantém o modelo fora da fronteira de confiança financeira.

## Custos

Os principais componentes cobrados são as invocações do modelo no Amazon Bedrock, as transições ou execuções do Step Functions, as invocações do Lambda, as requisições do API Gateway, as operações do DynamoDB e o armazenamento de logs.

Para laboratórios, mantenha mensagens curtas, use um modelo econômico, execute poucos testes e remova a stack ao terminar. O comando recomendado é:

```bash
sam delete
```

Os preços variam por região, modelo e volume. Consulte sempre as páginas oficiais antes de estimar uma implantação real.

## Evolução para produção

Uma versão mais completa poderia utilizar:

- Cardápio e estoque em tabelas próprias
- Pagamento com integração externa isolada
- SQS para processamento assíncrono
- EventBridge para eventos de mudança de status
- SNS ou WhatsApp para notificações
- Histórico de sessões com expiração
- Cache de prompts ou contexto
- Roteamento entre modelos por custo e complexidade
- Testes de carga, resiliência e segurança
