# Source - https://stackoverflow.com/a
# Posted by Scott Cooper, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-04, License - CC BY-SA 4.0

from shiny import App, render, ui
import matplotlib.pyplot as plt

# =================================================
max_plots = 5

app_ui = ui.page_fluid(
    ui.input_slider("n", "Number of plots", value=1, min=1, max=5),
    ui.output_ui("plots")
)


def server(input, output, session):
    def render_plot_func(j):
        @render.plot
        def f():
            fig = plt.plot(range(1, j + 1), range(1, j + 1))
            return fig

        return f

    @output
    @render.ui
    def plots():
        plot_output_list = []
        for i in range(1, input.n() + 1):
            plotname = f"plot{i}"

            plot_output_list.append(ui.output_plot(plotname))
            output(render_plot_func(i), id=plotname)
        return ui.TagList(plot_output_list)


app = App(app_ui, server)
