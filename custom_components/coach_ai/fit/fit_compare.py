"""Comparador FIT."""

from __future__ import annotations

from .fit_parser import FitParser


class FitCompare:
    """Compara dos archivos FIT."""

    def compare(
        self,
        garmin: bytes,
        coach: bytes,
    ) -> None:

        garmin_messages = FitParser(
            garmin,
        ).parse()

        coach_messages = FitParser(
            coach,
        ).parse()

        print()

        print("=========== COMPARACIÓN ===========")

        for index, (gm, cm) in enumerate(
            zip(
                garmin_messages,
                coach_messages,
            )
        ):

            print()

            print(
                f"Mensaje {index}"
            )

            print(
                f"Global Garmin: {gm['global']}"
            )

            print(
                f"Global Coach : {cm['global']}"
            )

            keys = sorted(
                set(gm["fields"])
                | set(cm["fields"])
            )

            for key in keys:

                gv = gm["fields"].get(key)
                cv = cm["fields"].get(key)

                if gv == cv:
                    continue

                print(
                    f" Campo {key}"
                )

                print(
                    f"   Garmin : {gv}"
                )

                print(
                    f"   Coach  : {cv}"
                )