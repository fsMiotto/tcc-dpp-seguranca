#Carrega o corpus da B2 filtrada
library(bibliometrix)

arquivo <- "../filtragem/resultados/scopus_busca2_2026-11-03_filtrado.csv"
M <- convert2df(arquivo, dbsource = "scopus", format = "csv")

#Documentos com palavras-chave dos autores separadas por vírgula em vez de ";" (corrigido só na memória)
dois_virgula <- c(
  "10.1016/j.spc.2025.01.014",
  "10.1016/j.procir.2024.10.150",
  "10.1007/978-3-032-16288-5_3"
)
i_virgula <- which(M$DI %in% dois_virgula)
stopifnot(length(i_virgula) == length(dois_virgula))

cat("\nCorrecao das palavras-chave com virgula (so na memoria):\n")
for (i in i_virgula) {
  termos <- trimws(unlist(strsplit(gsub(",", ";", M$DE[i]), ";")))
  novo <- paste(termos[termos != ""], collapse = "; ")
  cat("-", M$SR[i], "\n  antes:  ", M$DE[i], "\n  depois: ", novo, "\n")
  M$DE[i] <- novo
}

stopifnot(nrow(M) == 242)
print(table(M$PY))

cat(R.version.string, "| bibliometrix", as.character(packageVersion("bibliometrix")), "\n")
