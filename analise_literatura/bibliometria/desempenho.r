#Análise de desempenho: tabelas e gráficos de produção, fontes, autores e países
source("carregar.r")
source("utils/funcoes.r")

if (!interactive()) pdf(NULL)  #evita o Rplots.pdf no Rscript

dir.create("resultados/tabelas", recursive = TRUE, showWarnings = FALSE)
dir.create("resultados/graficos", recursive = TRUE, showWarnings = FALSE)

resultados <- biblioAnalysis(M)
S <- summary(resultados, k = 10)

#Autores contados pelo ID do Scopus ("Author full names": "Sobrenome, Nome (ID)")
bruto <- read.csv(arquivo, check.names = FALSE, stringsAsFactors = FALSE, encoding = "UTF-8")
stopifnot(nrow(bruto) == nrow(M))
assinaturas <- do.call(rbind, lapply(seq_len(nrow(bruto)), function(i) {
  pares <- trimws(strsplit(bruto$`Author full names`[i], ";")[[1]])
  pares <- pares[pares != ""]
  data.frame(doc = i, ID = sub(".*\\((\\d+)\\)$", "\\1", pares), Autor = sub("\\s*\\(\\d+\\)$", "", pares))
}))
assinaturas <- unique(assinaturas)
docs_por_id <- aggregate(doc ~ ID, data = assinaturas, FUN = length)
nomes <- assinaturas[!duplicated(assinaturas$ID), c("ID", "Autor")]
autores_id <- merge(docs_por_id, nomes, by = "ID")
names(autores_id)[names(autores_id) == "doc"] <- "Documentos"
autores_id <- autores_id[order(-autores_id$Documentos, autores_id$Autor), c("ID", "Autor", "Documentos")]

#Main Information com o número de autores pelo ID
n_autores <- nrow(autores_id)
docs_unico <- unique(assinaturas$doc[ave(assinaturas$doc, assinaturas$doc, FUN = length) == 1])
autores_unico <- length(unique(assinaturas$ID[assinaturas$doc %in% docs_unico]))
mi <- S$MainInformationDF
mi$Results[mi$Description == "Authors"] <- as.character(n_autores)
mi$Results[mi$Description == "Authors of single-authored docs"] <- as.character(autores_unico)
mi$Results[mi$Description == "Documents per Author"] <- format(nrow(M) / n_autores, digits = 3)

salvar(mi, "MainInformation.csv")
salvar(S$AnnualProduction, "AnnualProduction.csv")
salvar(S$MostRelSources, "MostRelSources.csv")
salvar(S$MostCitedPapers, "MostCitedPapers.csv")
#Países do autor correspondente, com a linha dos documentos sem país
sem_pais <- sum(is.na(resultados$CO) | resultados$CO == "")
paises_corresp <- as.data.frame(lapply(S$MostProdCountries, as.character), stringsAsFactors = FALSE)
paises_corresp <- rbind(paises_corresp, data.frame(Country = "Sem país identificado", Articles = as.character(sem_pais),
                                                   Freq = NA, SCP = NA, MCP = NA, MCP_Ratio = NA))
salvar(paises_corresp, "MostProdCountries.csv")
salvar(S$TCperCountries, "TCperCountries.csv")
salvar(S$MostRelKeywords, "MostRelKeywords.csv")
salvar(head(autores_id, 10), "MostProdAuthors.csv")

#Países de todos os autores
M_co <- metaTagExtraction(M, Field = "AU_CO", sep = ";")
paises <- sort(table(unlist(lapply(strsplit(M_co$AU_CO, ";"), function(x) unique(x[!is.na(x) & x != ""])))), decreasing = TRUE)
paises <- setNames(as.data.frame(paises, stringsAsFactors = FALSE), c("Country", "Documents"))
salvar(head(paises, 10), "CountriesAllAuthors.csv")

#Taxa de crescimento anual só dos anos completos (mesma fórmula do bibliometrix)
anos_completos <- 2022:2025
docs_ano <- table(factor(M$PY, levels = anos_completos))
taxa_completos <- ((docs_ano[[length(docs_ano)]] / docs_ano[[1]])^(1 / (length(anos_completos) - 1)) - 1) * 100
salvar(data.frame(Indicador = "Taxa de crescimento anual (%) - so anos completos",
                  Ano_inicial = min(anos_completos), Ano_final = max(anos_completos),
                  Documentos_ano_inicial = docs_ano[[1]], Documentos_ano_final = docs_ano[[length(docs_ano)]],
                  Valor = round(taxa_completos, 2)),
       "AnnualGrowthRate_anos_completos.csv")

bradford_res <- bradford(M)
salvar(bradford_res$table, "Bradford.csv")

graficos <- plot(x = resultados, k = 10, pause = FALSE)

#Bradford com as zonas em português
camada_zonas <- which(sapply(bradford_res$graph$layers, function(x) inherits(x$geom, "GeomText")))
bradford_res$graph$layers[[camada_zonas]]$aes_params$label <- c("Núcleo", "Zona 2", "Zona 3")
salvar_grafico(bradford_res$graph, "Bradford.png", x = "log(posição da fonte)", y = "Documentos acumulados")

#Nomes dos países em português
paises_pt <- c(GERMANY = "Alemanha", ITALY = "Itália", "UNITED KINGDOM" = "Reino Unido", AUSTRIA = "Áustria",
               PORTUGAL = "Portugal", CHINA = "China", NORWAY = "Noruega", AUSTRALIA = "Austrália",
               SWITZERLAND = "Suíça", USA = "Estados Unidos", KOREA = "Coreia do Sul", SWEDEN = "Suécia", NETHERLANDS = "Países Baixos")

salvar_grafico(graficos$MostProdCountries +
    ggplot2::scale_fill_discrete(breaks = c("SCP", "MCP"), labels = c("Um país (SCP)", "Vários países (MCP)")) +
    ggplot2::scale_x_discrete(limits = graficos$MostProdCountries$scales$get_scales("x")$limits, labels = paises_pt),
  "MostProdCountries.png", x = "País", y = "Documentos", fill = "Colaboração")

#Gráfico da produção anual só até o ano da busca
protocolo <- read.csv("../filtragem/buscas/protocolo_busca.csv", fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
ano_busca <- as.integer(substr(protocolo$Data[protocolo$Busca == "B2"], 1, 4))
stopifnot(length(ano_busca) == 1, !is.na(ano_busca))
graficos$AnnualScientProd$data <- subset(graficos$AnnualScientProd$data, Year <= ano_busca)
salvar_grafico(graficos$AnnualScientProd +
    ggplot2::scale_x_continuous(breaks = min(M$PY, na.rm = TRUE):ano_busca) +
    ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 0, hjust = 0.5)),
  "AnnualProduction.png", x = "Ano", y = "Documentos")
