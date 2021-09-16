require('gtools')
require('optparse')
require('sqldf')

option_list <- list(
  make_option(c("-i", "--input"), type = "character", help = "input directory")
)

opt_parser <- OptionParser(option_list = option_list)
args <- parse_args(opt_parser)

if (length(args) < 1) {
  print_help(opt_parser)
  stop()
}

base <- args$input

pairs <- data.frame()
rank.cache <- c()

knowledge_levels <- list.dirs(base, recursive = FALSE, full.names = FALSE)

print(paste(knowledge_levels, sep=", "))

for (knowledge_level in knowledge_levels)
{
  print(c("knowledge_level", knowledge_level))
  dir_k <- paste(base, knowledge_level, sep="/")

  iterations <- list.dirs(dir_k, recursive = FALSE, full.names = FALSE)

  for (iteration in iterations)
  {
    print(c("iterations", iteration))
    
    dir_i <- paste(dir_k, iteration, sep="/")

    confidence_levels <- list.dirs(dir_i, recursive = FALSE, full.names = FALSE)

    for (confidence_level in confidence_levels)
    {
      print(c("k_l", knowledge_level, "i", iteration, "c_l", confidence_level))
      dir_c <- paste(dir_i, confidence_level, sep="/")
      
      experiments <- list.dirs(dir_c, recursive = FALSE, full.names = FALSE)

      for (experiment in experiments)
      {
      	print(experiment)
        dir_e <- paste(dir_c, experiment, sep="/")
        
        programs <- list.dirs(dir_e, recursive = FALSE, full.names = FALSE)
        
        for (program in programs)
        {
          print(program)
          dir_p <- paste(dir_e, program, sep="/")

          versions <- list.dirs(dir_p, recursive = FALSE, full.names = FALSE)
              
          for (version in versions)
          {
            dir_v <- paste(dir_p, version, sep="/")

            files <- list.files(dir_v, recursive = FALSE)
          
            original.csv <- paste(dir_v, head(files, 1), sep="/")
            ifl.csv <- paste(dir_v, tail(files, 1), sep="/")
            
            pvkey <- paste(program, version, sep="-")
            
            if (pvkey %in% names(rank.cache))
            {
              o.rank <- rank.cache[[pvkey]]
            }
            else
            {
              scores <- read.csv(
                file = original.csv,
                sep = ";",
                row.names = "Name"
              )
              scores <- scores[with(scores, order(-scores$Score, row.names(scores))), ]
              scores$rank <- rank(-scores$Score)

              o.rank <- head(scores[scores$Faulty=="True",],1)$rank
              
              rank.cache <- c(rank.cache, c(pvkey=o.rank))
            }

            scores_ <- read.csv(
              file = ifl.csv,
              sep = ";",
              row.names = "Name"
            )
            scores_ <- scores_[with(scores_, order(-scores_$Score, row.names(scores_))), ]
            scores_$rank <- rank(-scores_$Score)

            #i.rank <- head(scores_[scores_$Faulty=="True",],1)$rank
            last_iteration <- strtoi(unlist(strsplit(tail(files, 1), "[.]"))[1])
            i.rank <- ifelse(last_iteration == 1, head(scores_[scores_$Faulty=="True",], 1)$rank, last_iteration - 1)

            num.of.ce <- nrow(scores)

            row <- data.frame(
              Knowledge = knowledge_level,
              Iteration = iteration,
              Confidence = confidence_level,
              Experiment = experiment,
              Program = program,
              Version = version,
              Start = o.rank,
              End = i.rank,
              StartN = o.rank / num.of.ce,
              EndN = i.rank / num.of.ce
            )
            pairs <- rbind(pairs, row)
          }
        }
      }
    }
  }
}

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

write.table(
  pairs,
  file = paste(gsub("/", "-", base), "csv", sep="."),
  sep = ";",
  dec = ",",
  eol = "\n",
  row.names = FALSE
)
