#!/usr/bin/env Rscript
require('gtools')
require('optparse')

option_list <- list(
  make_option(c("-e", "--experiment"), type = "character", help = "name of the experiment"),
  make_option(c("-s", "--score"), type = "character", help = "short name of the score metric"),
  make_option(c("-i", "--input"), type = "character", help = "input directory"),
  make_option(c("-d", "--debug"), type = "logical", default = FALSE, action = "store_true", help = "whether to create data for debugging")
)

opt_parser <- OptionParser(option_list = option_list)
args <- parse_args(opt_parser)

if (length(args) < 4) {
  print_help(opt_parser)
  stop()
}

base <- paste(args$input, args$score, args$experiment, sep = "/")

k <- 1
pairs <- data.frame()

progs <- list.dirs(base, recursive = FALSE, full.names = FALSE)

for (prog in progs) {
  print(prog)
  if (args$debug) {
    pdf(file = paste(args$score, args$experiment, prog, "iterations.pdf", sep = "-"), height = 10, width = 20)
  }
  
  versions = list.dirs(paste(base, "/", prog, sep = ""), recursive = FALSE, full.names = FALSE)
  
  for (version in mixedsort(versions)) {
    print(version)

    ranks <- c()

    iterations = list.files(paste(base, "/", prog, "/", version, sep = ""), recursive = FALSE)

    for (i in mixedsort(iterations)) {
      csv.file <- paste(base, "/", prog, "/", version, "/", i, sep = "")
      print(csv.file)

      if (!file.exists(csv.file)) {
        print("not found [skip]")
        next
      }

      scores <- read.csv(
        file = csv.file,
        sep = ";",
        row.names = "Name"
      )
      scores <- scores[with(scores, order(-scores$Score, row.names(scores))), ]
      scores$rank <- rank(-scores$Score)

      pos <- barplot(
        scores$Score,
        #ylim = c(0,1),
        xlab = "Code Elements",
        ylab = "Score",
        col = ifelse(scores$Faulty == "True", "red", "lightblue"),
        main = paste(prog, "(", "Version", version, ")"),
        sub = paste("Iteration", sub(".csv", "", i)),
        bor = FALSE
      )

      axis_labels <- c("")
      axis_label_positions <- c(pos[1])
      for (i in 1:length(pos)) {
        if (scores$Faulty[i] == "True") {
          axis_labels <- c(axis_labels, row.names(scores)[i])
          axis_label_positions <- c(axis_label_positions, pos[i])
          ranks <- c(ranks, scores$rank[i])
        }
      }
      axis_labels <- c(axis_labels, "")
      axis_label_positions <- c(axis_label_positions, pos[length(pos)])
      
      axis(1, at = axis_label_positions, labels = axis_labels, las = 2)

      text(
        x = pos,
        y = scores$Score,
        label = mapply(function(s, r, f) ifelse(f == "True", paste(s, "[", r, "]"), ""), scores$Score, scores$rank, scores$Faulty),
        pos = 3,
        cex = 0.8,
        col = "red"
      )
    } # end iterations

    if (args$debug) {
      plot(
        ranks,
        type = "b",
        main = "Timeline",
        xlab = "Iteration",
        ylab = "Rank",
        xaxt = "n"
      )
    }

    #TODO(fhorvath): az x-y tengely arányosítás

    ticks <- seq(1, length(ranks))
    
    axis(1, at = ticks, labels = ticks - 1)

    text(
      x = ticks,
      y = ranks,
      labels = ranks,
      pos = 1
    )

    if (length(ticks) > 1) {
      text(
        x = ticks + 0.5,
        y = 0.5 * (head(ranks, -1) + tail(ranks, -1)),
        labels = head(ranks, -1) - tail(ranks, -1),
        pos = 3,
        col = "red"
      )
    }

    num_of_ce = nrow(scores)
    end <- ifelse(length(ranks) == 1, tail(ranks, 1), length(ranks) - 1)
    row <- data.frame(Program = prog, Version = version, Start = ranks[1], End = end, StartN = ranks[1] / num_of_ce, EndN = end / num_of_ce)
    pairs <- rbind(pairs, row)
  } # end versions

  if (args$debug) {
    dev.off()
  }
} # end programs

pairs$Diff <- pairs$End - pairs$Start
pairs$DiffN <- pairs$EndN - pairs$StartN

fn <- function(start, end) {
  if (start > 10 && end <= 10 && end > 5) {
    1
  } else if (start > 10 && end <= 5) {
    2
  } else if (start > 5 && start <= 10 && end <= 5) {
    3
  } else {
    0
  }
}

pairs$Class <- mapply(fn, pairs$Start, pairs$End)

print(pairs)

pdf(paste(args$score, args$experiment, "summary.pdf", sep = "-"))

lim <- c(0, max(pairs$Start, pairs$End))

plot(
  x = pairs$Start,
  y = pairs$End,
  main = paste(args$score, "vs iFL ranks"),
  xlab = args$score,
  ylab = "iFL",
  xlim = lim,
  ylim = lim
)

plot(
  x = pairs$StartN,
  y = pairs$EndN,
  main = paste(args$score, "vs iFL ranks\n(normalized with no. CEs)"),
  xlab = paste("% of CEs (", args$score, ")", sep = ""),
  ylab = "% of CEs (iFL)",
  xlim = c(0, 1),
  ylim = c(0, 1)
)

write.table(
  pairs,
  file = paste(args$score, args$experiment, "summary.csv", sep = "-"),
  sep = ";",
  dec = ",",
  eol = "\n",
  row.names = FALSE
)

dev.off()
