import logging
from pathlib import Path

def rewrite_psa_file(psa_file: Path, latitude: float):
    """Rewrite the psa file
    * deletes NameAppend value attribute text
    * substitutes latitude into Latitude value attribute
    """
    with open(psa_file, "r") as f:
        get_all = f.readlines()

    try:
        # open new psa file and rewrite, changing lines if NameAppend or Latitude are found
        with open(psa_file, "w") as f:
            # START THE NUMBERING FROM 1 (by default it begins with 0)
            for i, line in enumerate(get_all, 0):
                if '<NameAppend value="' in line:
                    f.writelines('  <NameAppend value="" />\n')
                elif "<Latitude value=" in line:
                    f.writelines(
                        f'<Latitude value="{latitude}" />\n'
                    )
                    logging.info(f"Latitude set to {latitude} in PSA file {psa_file}")
                else:
                    f.writelines(line)
    except TypeError:
        # FIXME brittle, shouldn't this copy the original?
        logging.warning("TypeError rewriting", psa_file)
        with open(psa_file, "w") as f:
            for i, line in enumerate(get_all, 0):
                f.writelines(line)
