# Segurança

- Não disponibilizar o Excel original no bucket lido pelo painel.
- Usar bucket privado e `service_role` apenas no servidor.
- Rotacionar imediatamente qualquer chave publicada por engano.
- Manter resultados por escola agregados e impedir detalhamento de células pequenas.
- Validar coordenadas antes da publicação.
- Registrar versão, hash e horário de atualização da fonte.
