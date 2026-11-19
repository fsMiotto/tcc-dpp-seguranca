#Mapeamento científico: trend topics, mapa temático e rede de co-ocorrência das palavras-chave dos autores (DE)
source("carregar.r")
source("utils/funcoes.r")

if (!interactive()) pdf(NULL)  #evita o Rplots.pdf no Rscript

#---------------------------------------------------------------------------
#Parâmetros
#---------------------------------------------------------------------------
pasta_rede        <- "resultados/co-ocorrencia"
pasta_mapa        <- "resultados/mapa_tematico"
pasta_tt          <- "resultados/trend_topics"
arquivo_sinonimos <- "utils/sinonimos.csv"            #um grupo por linha, separado por ";"; o primeiro termo fica
termos_removidos  <- c("digital product passport")

#Trend Topics
tt_timespan <- NULL
tt_min_freq <- 2
tt_n_items  <- 5

#Rede de co-ocorrência
rede_n         <- 50
rede_normalize <- "association"
rede_cluster   <- "louvain"
rede_type      <- "auto"
rede_isolates  <- TRUE
rede_edges_min <- 2
rede_seed      <- 1234

#Mapa temático
mt_n         <- 250
mt_minfreq   <- 5
mt_n_labels  <- 3
mt_cluster   <- "louvain"
mt_seed      <- 1234
mt_size      <- 0.3
mt_repulsion <- 0.5
mt_alpha     <- 0.5
mt_repel     <- FALSE

sinonimos <- readLines(arquivo_sinonimos, warn = FALSE)
sinonimos <- sinonimos[trimws(sinonimos) != ""]

for (pasta in c(pasta_rede, pasta_mapa, pasta_tt)) dir.create(pasta, recursive = TRUE, showWarnings = FALSE)

#---------------------------------------------------------------------------
#Trend Topics
#---------------------------------------------------------------------------
tt <- fieldByYear(M, field = "DE", timespan = tt_timespan, min.freq = tt_min_freq,
                  n.items = tt_n_items, remove.terms = termos_removidos, synonyms = sinonimos, graph = FALSE)
#Gráfico girado (coord_flip): x são os termos e y os anos
anos_tt <- c(min(M$PY, na.rm = TRUE),
             max(tt$df_graph[, c("year_q1", "year_med", "year_q3")], na.rm = TRUE))
salvar_grafico(tt$graph +
    ggplot2::scale_y_continuous(breaks = anos_tt[1]:anos_tt[2], limits = anos_tt) +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 0, hjust = 0.5)) +
    ggplot2::guides(size = ggplot2::guide_legend(order = 1, title = "Frequência")),
  "trend_topics.png", x = "Termo", y = "Ano", pasta = pasta_tt)
salvar(tt$df_graph, "trend_topics.csv", pasta = pasta_tt)

#---------------------------------------------------------------------------
#Mapa temático
#---------------------------------------------------------------------------
mt <- thematicMap(M, field = "DE", n = mt_n, minfreq = mt_minfreq, n.labels = mt_n_labels, size = mt_size,
                  community.repulsion = mt_repulsion, alpha = mt_alpha, repel = mt_repel,
                  cluster = mt_cluster, seed = mt_seed, remove.terms = termos_removidos, synonyms = sinonimos)
#Quadrantes em português (ordem: inferior esq., superior esq., inferior dir., superior dir.)
camada_quadrantes <- which(sapply(mt$map$layers, function(l) inherits(l$geom, "GeomText") && is.null(l$mapping$label)))
mt$map$layers[[camada_quadrantes]]$aes_params$label <- c("Temas emergentes\nou em declínio", "Temas de nicho",
                                                         "Temas básicos", "Temas motores")
#Rótulos dos temas com ggrepel, para não se sobreporem
camada_rotulos <- which(sapply(mt$map$layers, function(l) inherits(l$geom, "GeomText") && !is.null(l$mapping$label)))
mt$map$layers[[camada_rotulos]] <- ggrepel::geom_text_repel(
  ggplot2::aes(group = "NA", label = ifelse(freq > 1, unlist(tolower(name_full)), "")),
  size = 3 * (1 + mt_size), colour = adjustcolor("black", alpha.f = 0.7), bg.color = "white", bg.r = 0.15,
  point.size = NA, box.padding = 0.3, max.overlaps = Inf, min.segment.length = 0.3, segment.colour = "grey60", seed = mt_seed)
salvar_grafico(mt$map, "mapa_tematico.png", x = "Centralidade", y = "Densidade", pasta = pasta_mapa, altura = 7)
salvar(mt$clusters, "mapa_tematico.csv", pasta = pasta_mapa)
salvar(mt$words, "mapa_tematico_palavras.csv", pasta = pasta_mapa)

#---------------------------------------------------------------------------
#Rede de co-ocorrência
#---------------------------------------------------------------------------
NetMatrix <- biblioNetwork(M, analysis = "co-occurrences", network = "author_keywords", n = rede_n,
                           sep = ";", remove.terms = termos_removidos, synonyms = sinonimos)
#O networkPlot calcula a rede; o desenho é refeito por rede_ggplot()
rede <- networkPlot(NetMatrix, normalize = rede_normalize, cluster = rede_cluster, type = rede_type,
                    remove.isolates = rede_isolates, edges.min = rede_edges_min,
                    seed = rede_seed, Title = "", verbose = FALSE)
salvar_grafico(rede_ggplot(rede, seed = rede_seed), "rede.png", x = NULL, y = NULL, pasta = pasta_rede, largura = 10, altura = 8)
salvar(rede$cluster_res, "rede.csv", pasta = pasta_rede)
