#!/usr/bin/env bash
# This is a helper script which executes the SourceMeterCPP binary with
# arguments that produce the least amount of junk during/after analysis.

if [ $# -ne 3 ]; then
  echo -e "Usage: ${0} <projectName> <buildScript> <resultsDir>"
  exit 1
fi

# Change this to the appropriate path which contains the SourceMeterCPP binary.
BASEDIR="/home/fhorvath/Work/sm/SourceMeter-8.2.0-x64-linux/CPP"

if [ ! -f "$BASEDIR/SourceMeterCPP" ]; then
  echo "BASEDIR must contain the SourceMeterCPP binary"
  exit 2
fi

echo "-/usr/" >${BASEDIR}/soft-filter.txt

${BASEDIR}/SourceMeterCPP \
  -projectName=${1} \
  -buildScript=${2} \
  -resultsDir=${3} \
  -externalSoftFilter=${BASEDIR}/soft-filter.txt \
  -runMetricHunter=false \
  -runFaultHunter=false \
  -runDCF=false \
  -runMET=false \
  -cloneGenealogy=false \
  -cleanResults=0 \
  -cleanProject=.
