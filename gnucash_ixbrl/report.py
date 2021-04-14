
from . format import NegativeParenFormatter
from . period import Period
from . ixbrl import IxbrlReporter
import io

class TextReporter:

    def output(self, worksheet, out):

        fmt = NegativeParenFormatter()

        def format_number(n):
            if abs(n.value) < 0.001:
                return "- "
            return fmt.format("{0:.2f}", n.value)

        ds = worksheet.get_dataset()

        periods = ds.periods
        sections = ds.sections

        out.write(fmt.format("{0:40}  ", ""))
        for period in periods:
            out.write(fmt.format("{0:>10} ", period.name + " "))

        out.write("\n")

        for section in sections:

            out.write("\n")

            if section.total == None and section.items == None:

                out.write(fmt.format("{0:40}: ", section.header))

                for period in periods:
                    out.write(fmt.format("{0:>10} ", " - "))

                out.write("\n")
                

            elif section.items == None:

                out.write(fmt.format("{0:40}: ", section.header))

                for i in range(0, len(periods)):

                    s = format_number(section.total.values[i])
                    out.write("{0:>10} ".format(s))

                out.write("\n")

            else:

                out.write(fmt.format("{0}:\n", section.header))

                for item in section.items:
                    
                    out.write(fmt.format("  {0:38}: ", item.description))

                    for i in range(0, len(periods)):

                        s = format_number(item.values[i])
                        out.write(fmt.format("{0:>10} ", s))

                    out.write("\n")

                out.write(fmt.format("{0:40}: ", "Total"))

                for i in range(0, len(periods)):

                    s = format_number(section.total.values[i])
                    out.write(fmt.format("{0:>10} ", s))

                out.write("\n")


