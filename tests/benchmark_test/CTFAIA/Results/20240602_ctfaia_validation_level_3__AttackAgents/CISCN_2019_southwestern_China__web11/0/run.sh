#
echo RUN.SH STARTING !#!#
export AUTOGEN_TESTBED_SETTING="Docker"

umask 000
echo "autogenbench version: 0.0.3" > timestamp.txt

# Run the global init script if it exists
if [ -f global_init.sh ] ; then
    . ./global_init.sh
fi

# Run the scenario init script if it exists
if [ -f scenario_init.sh ] ; then
    . ./scenario_init.sh
fi

# Run the scenario
pip install -r requirements.txt
echo SCENARIO.PY STARTING !#!#
timeout --preserve-status --kill-after 1830s 1800s python scenario.py
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo SCENARIO.PY EXITED WITH CODE: $EXIT_CODE !#!#
else
    echo SCENARIO.PY COMPLETE !#!#
fi

# Clean up
if [ -d .cache ] ; then
    rm -Rf .cache
fi

if [ -d __pycache__ ] ; then
    rm -Rf __pycache__
fi

# Run the scenario finalize script if it exists
if [ -f scenario_finalize.sh ] ; then
    . ./scenario_finalize.sh
fi

# Run the global finalize script if it exists
if [ -f global_finalize.sh ] ; then
    . ./global_finalize.sh
fi

echo RUN.SH COMPLETE !#!#
