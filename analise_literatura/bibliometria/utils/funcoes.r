#Funções usadas por desempenho.r e mapeamento.r

#Limpa a tabela (espaços e números como texto) e grava em CSV
salvar <- function(df, nome, pasta = "resultados/tabelas") {
  df <- as.data.frame(df, stringsAsFactors = FALSE)
  names(df) <- trimws(names(df))
  df[] <- lapply(df, function(x) type.convert(trimws(as.character(x)), as.is = TRUE))
  write.csv(df, file = file.path(pasta, nome), row.names = FALSE)
}

#Grava o gráfico sem título, subtítulo, nota e logo, com os eixos traduzidos
salvar_grafico <- function(g, nome, x, y, ..., pasta = "resultados/graficos", largura = 8, altura = 6) {
  g$layers <- g$layers[!sapply(g$layers, function(l) inherits(l$geom, "GeomCustomAnn"))]
  g <- g + ggplot2::labs(title = NULL, subtitle = NULL, caption = NULL, x = x, y = y, ...)
  ggplot2::ggsave(file.path(pasta, nome), g, width = largura, height = altura, dpi = 300)
}

#Redesenha a rede do networkPlot em ggplot (mesmas posições, cores e clusters), com rótulos sem sobreposição
#Tamanho do nó = grau ponderado (deg); espessura da ligação = peso (width)
rede_ggplot <- function(rede, seed = 1234) {
  g <- rede$graph
  lay <- igraph::graph_attr(g, "layout")
  v <- igraph::as_data_frame(g, "vertices"); v$x <- lay[, 1]; v$y <- lay[, 2]
  e <- unique(igraph::as_data_frame(g, "edges")[, c("from", "to", "width", "color", "lty")])
  e <- e[order(e$width), ]  #ligações fortes por cima
  e$x <- v$x[match(e$from, v$name)]; e$y <- v$y[match(e$from, v$name)]
  e$xend <- v$x[match(e$to, v$name)]; e$yend <- v$y[match(e$to, v$name)]
  ggplot2::ggplot() +
    ggplot2::geom_segment(data = e, ggplot2::aes(x, y, xend = xend, yend = yend, linewidth = width), colour = e$color,
                          linetype = ifelse(e$lty == 1, "solid", "dashed")) +
    ggplot2::geom_point(data = v, ggplot2::aes(x, y, size = deg), fill = v$color, colour = "grey30", shape = 21) +
    ggrepel::geom_text_repel(data = v, ggplot2::aes(x, y, label = name), size = 3.6, colour = "grey15",
                             bg.color = "white", bg.r = 0.15, max.overlaps = Inf, box.padding = 0.5,
                             min.segment.length = 0.3, segment.colour = "grey60", seed = seed) +
    ggplot2::scale_size(range = c(2, 22)) +
    ggplot2::scale_linewidth(range = c(0.2, 2)) +
    ggplot2::scale_x_continuous(expand = ggplot2::expansion(mult = 0.15)) +
    ggplot2::theme_void() +
    ggplot2::theme(legend.position = "none", plot.background = ggplot2::element_rect(fill = "white", colour = NA))
}
