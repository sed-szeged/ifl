library('sqldf')
library('optparse')
library('lattice')

option_list <- list(
  make_option(c("-i", "--input"), type = "character", help = "input csv")
)

opt_parser <- OptionParser(option_list = option_list)
args <- parse_args(opt_parser)

if (length(args) < 1) {
  print_help(opt_parser)
  stop()
}

df <- read.csv(
  file = args$input,
  sep = ";"
)

agg <- sqldf("
  SELECT
    Knowledge,
    Confidence,
    AVG(Start) AS Start,
    AVG(End) AS End,
    AVG(Diff) AS Diff,
    AVG(REPLACE(StartN, ',', '.')) AS StartN,
    AVG(REPLACE(EndN, ',', '.')) AS EndN,
    AVG(REPLACE(DiffN, ',', '.')) AS DiffN
  FROM
    df
  WHERE
    Knowledge >= 20 AND Confidence >= 20
  GROUP BY
    Knowledge,
    Confidence
  ORDER BY
    Knowledge ASC,
    Confidence ASC
")

#for (k in seq(0, 100, 10))
#{
#  row <- data.frame(
#    Knowledge = k,
#    Confidence = 0,
#    Start = 0,
#    End = 0,
#    StartN = 0,
#    EndN = 0,
#    Diff = 0,
#    DiffN = 0
#  )
#  agg <- rbind(agg, row)
#}

#agg <- sqldf("SELECT * FROM agg ORDER BY Knowledge ASC, Confidence ASC")

#print(agg)

knwl <- sqldf("SELECT DISTINCT Knowledge FROM agg")
cnfd <- sqldf("SELECT DISTINCT Confidence FROM agg")

pdf(gsub(".csv", ".pdf", args$input))

lab.main <- strsplit(args$input, "[-.]")[[1]][2]
lim.z <- c(-70, 200)
lim.y <- c(-70, 50)
#lim.z <- c(-20, 5)
#lim.y <- c(-20, 0)

x <- unique(agg$Confidence)
y <- unique(agg$Knowledge)
z <- matrix(agg$Diff, nrow=nrow(cnfd), ncol=nrow(knwl))

z.min <- min(z)

print(c(x, y, z.min))

checkColor <- function(matrix, limit)
{
  se <- matrix[-1, -1] <= limit
  sw <- matrix[-1, -ncol(matrix)] <= limit
  ne <- matrix[-nrow(matrix), -1] <= limit
  nw <- matrix[-nrow(matrix), -ncol(matrix)] <= limit

  return(se & sw & ne & nw)
}

filter80 <- as.integer(checkColor(z, z.min * 0.8))
filter90 <- as.integer(checkColor(z, z.min * 0.9))
colorIndices <- filter80 + filter90 + 1

mapColors <- function(elem, colors)
{
  return(colors[elem])
}

colors <- sapply(colorIndices, mapColors, c("orange", "yellow", "green"))

print(filter80)
print(filter90)
print(colorIndices)
print(colors)

persp(
  x=x,
  y=y,
  z=z,
  theta=135,
  main=lab.main,
  xlab="Confidence",
  ylab="Knowledge",
  zlab="Expense Diff.",
  ticktype="detailed",
  zlim=lim.z,
  shade=1,
  col=colors
)

# FIXED CONFIDENCE × VARIABLE KNOWLEDGE

k <- sqldf("
  SELECT
    *
  FROM
    agg
  WHERE
    Confidence IS 100
")

#print(k)

p <- plot(
  x = k$Knowledge,
  y = k$Diff,
  main=lab.main,
  xlab = "Knowledge",
  ylab = "Expense Diff.",
  ylim=lim.y,
  type = "o"
)
text(
  x = k$Knowledge,
  y = k$Diff,
  labels = format(k$Diff, digits=2, nsmall=2),
  pos = 3,
  cex = 0.6
)
grid(col = "black")

# FIXED KNOWLEDGE × VARIABLE CONFIDENCE

c <- sqldf("
  SELECT
    *
  FROM
    agg
  WHERE
    Knowledge IS 100
")

#print(c)

p <- plot(
  x = c$Confidence,
  y = c$Diff,
  main=lab.main,
  xlab = "Confidence",
  ylab = "Expense Diff.",
  ylim=lim.y,
  type = "o"
)
text(
  x = c$Confidence,
  y = c$Diff,
  labels = format(c$Diff, digits=2, nsmall=2),
  pos = 3,
  cex = 0.6
)
grid(col = "black")

dev.off()
