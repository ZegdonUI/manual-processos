# Manual de Processos — referências

## Inspiração
- Vitrine Wix: https://www.wix.com/wix-platform/explore-dashboard/site/chico-santos?lang=pt
- Site real: https://www.chicosantos.org/en (template Wix nº 2213)
- Estilo: galeria minimalista, muito branco, menu lateral como índice (lista de obras → aqui lista de processos), página única por item, rodapé só com contato.
- Original usa Courier (corpo 15px), DIN Next Light / Brandon Grotesque Light, preto `#080808`, cinza `#414141`, destaque terracota `#B0765D`.

## Identidade aplicada (Privalia)
Tirada do CSS de privalia.com.br.

| Token | Cor |
|---|---|
| Rosa (destaque) | `#EA2D79` |
| Grafite (títulos) | `#212121` |
| Texto | `#2E2E2E` |
| Cinza linhas | `#E5E5E5` |
| Fundo alternativo | `#F4F4F4` |

Fontes: Poppins (títulos e corpo) + IBM Plex Mono (códigos, rótulos, como o Courier do original).

## Arquivos
- `index.html` — o manual inteiro (HTML + CSS + JS num arquivo só).
- `servidor.py` — servidor (Python, sem dependências). Serve o site e recebe upload/troca/remoção de imagens de **qualquer pessoa com o link** (sem login). `--somente-leitura` volta a limitar a edição a localhost.
  - Removidas/trocadas não são apagadas: vão para `img/_lixeira/` (`<processo>__<secao>__<arquivo>`).
  - Troca/remoção conferem o nome do arquivo; se outra pessoa mexeu antes, recusa (409) e a página recarrega a lista.
- `abrir.bat` — sobe `servidor.py` só para este PC e abre http://localhost:8080.
- `compartilhar.bat` — sobe `servidor.py` na rede (porta 8080) e mostra o link. Fechar a janela para de compartilhar.
- `textos.json` — textos editados pelo site (botão "Editar página"). Tem prioridade sobre o texto padrão no `index.html`. Chave = pasta da seção (`fashion/top-amostra`) ou `<area>/<origem>` (regras gerais); campos `intro`, `vista.N`, `obs.N`, `regra`, `exemplosTitulo`, `descricao`.
- `textos-historico.jsonl` — toda alteração de texto (data, antes, depois): dá para recuperar qualquer versão.
- `img/manifesto.json` — lista das imagens por seção (`"fashion/top-amostra": { vistas, usos, exemplos }`). Gerado pelo upload.
- `img/<processo>/<secao>/` — imagens enviadas. Todas cortadas no navegador para 3:4, 1200×1600 JPEG.

## Estrutura: Área › Amostra/Fornecedor › Categoria › Seção
- Áreas: Geradores de Imagem, Stylist, Fotógrafos — todas com a mesma estrutura, nada fica "em breve".
- Dentro da área, primeiro escolhe-se **Amostra** ou **Fornecedor** (regras diferentes); as categorias e seções (`CATEGORIAS`) são as mesmas em todas as áreas e nos dois lados. Textos e imagens são separados por página.
- Rotas: `#geradores` → `#geradores/amostra` → `#geradores/amostra/fashion/top`.
- Na página da seção, o seletor Amostra | Fornecedor leva à mesma categoria/seção do outro lado.
- Categorias e seções:
  - Fashion: Top, Bottom, Peça inteira
  - Still: Sapato, Bolsas, Acessórios, Óculos
  - Kids: Top, Bottom, Peça inteira, Conjunto, Bebês
  - Underwear, Beachwear: sem seções = página única (rota `.../underwear/geral`).
- Links antigos (`#fashion/top-amostra`, `#still`…) redirecionam para Geradores › Amostra.
- Textos padrão só existem em `PADROES` (hoje: Geradores › Amostra › Fashion › Top); o resto começa vazio e é preenchido pelo site.

## Seções com imagens (ex.: Geradores › Amostra › Fashion › Top)
- Ordem padrão de toda seção: `intro` + `vistas` (nomes, posição fixa) → `exemplosTitulo` + galeria `exemplos` ("Mais exemplos") → `regra` ("!") + galeria `usos`. O bloco "!" vai virar "Qualidade" no futuro.
- Pasta/chave das imagens: `<area>-<origem>-<categoria>/<secao>` (ex.: `geradores-fornecedor-fashion/top`). O Top de Amostra usa `pasta: "fashion/top-amostra"` (pasta original).
- Fonte do conteúdo: Slides "guias rascunho", slides 4–6.

## Onde preencher
No começo do `<script>` do `index.html`:
- `MANUAL` — versão, contato, texto "Sobre".
- `AREAS`, `ORIGENS`, `CATEGORIAS` (com `secoes`) — estrutura, compartilhada por todas as áreas.
- `PADROES` — textos iniciais por página (`"area/origem/categoria/secao"`) e `pasta` de imagens quando diferente do padrão.
- `VISTAS_PADRAO` — nomes das 4 vistas (editáveis por página no site).

## Compartilhar
- Link só abre na rede/VPN Privalia, com o PC ligado e `compartilhar.bat` aberto.
- Se colega não conseguir abrir: firewall do Windows (perfil Domínio) pode bloquear a porta 8080 → pedir liberação ao TI.
- Alternativa futura (não adotada): publicar na Vercel com proteção por login.

## Pendente (quando subir para cloud)
- Acesso admin para alison.bezerra@privalia.com e graciele.melo@privalia.com: adicionar/remover imagens, alterar textos, criar seções. Exige login + armazenamento; o HTML estático atual não suporta.
