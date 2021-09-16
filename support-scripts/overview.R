#!/usr/bin/env Rscript

base <- "."

csv.files <- list.files(base, pattern = "*-summary.csv", recursive = FALSE, full.names = FALSE)

overview = data.frame()

for (csv.file in csv.files) {
  print(csv.file)

  parts <- strsplit(csv.file, "-")
  data <- read.csv2(file = csv.file)

  N <- print(nrow(data))

  row <- data.frame(
    Score = parts[[1]][1],
    Experiment = parts[[1]][2],
    "Avg Score Rank" = mean(data$Start),
    "Avg iFL Rank" = mean(data$End),
    "Avg Rank Diff" = mean(data$Diff),
    "Avg Score Rank (norm.)" = mean(data$StartN),
    "Avg iFL Rank (norm.)" = mean(data$EndN),
    "Avg Rank Diff (norm.)" = mean(data$DiffN),
    "10 to 5_10" = nrow(subset(data, Class == 1)),
    "10 to 5" = nrow(subset(data, Class == 2)),
    "5_10 to 5" = nrow(subset(data, Class == 3)),
    "10 to 5_10 (%)" = nrow(subset(data, Class == 1))/N,
    "10 to 5 (%)" = nrow(subset(data, Class == 2))/N,
    "5_10 to 5 (%)" = nrow(subset(data, Class == 3))/N
  )

  overview <- rbind(overview, row)
}

print(overview)

write.table(
  overview,
  file = "overview.csv",
  sep = ";",
  dec = ",",
  eol = "\n",
  row.names = FALSE
)
