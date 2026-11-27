"""Calculator command handlers mixin."""


class CalculatorHelper:
    """Default handlers for calculator commands."""

    def _help(self, op: str | None = None) -> None:
        """Show all commands, or details for one command."""
        if op is None:
            for key, value in self.command_info.items():
                self.logger.info("%s : %s", key, value[1])
        elif op in self.command_info:
            self._command_help(op)
        else:
            self.logger.warning(f"Unknown command '{op}'. Type 'help' to see options.")

    def _command_help(self, op: str) -> None:
        """Show description and example for one command."""
        self.logger.info("%s : %s %s", op, self.command_info[op][1], self.command_info[op][2])

    def _print_history(self) -> None:
        """Print every past calculation."""
        self.logger.info("%s", self.history)

    def _print_stats(self) -> None:
        """Print count, min, max, and average of results."""
        stats = self.history.stats()
        if stats["count"] == 0:
            self.logger.info("No calculations yet")
            return
        self.logger.info(f"count: {stats['count']}, min: {stats['min']}, "
                         f"max: {stats['max']}, average: {stats['average']:.2f}")

    def _clear_history(self) -> None:
        """Clear the history and persist it."""
        self.history.clear()
        try:
            self.history.save(self.data_file, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save history: {e}")
        self.logger.info("History cleared")

    def _memory_store(self) -> None:
        """Store the last result in memory."""
        last = self.history.last_result()
        if last is None:
            self.logger.info("No previous result yet")
            return
        self.memory = last
        try:
            self.history.save(self.data_file, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save memory: {e}")
        self.logger.info(f"Stored {last} in memory")

    def _memory_recall(self) -> None:
        """Print the stored memory value."""
        if self.memory is None:
            self.logger.info("Memory is empty")
            return
        self.logger.info("%s", self.memory)

    def _memory_clear(self) -> None:
        """Clear memory and persist it."""
        self.memory = None
        try:
            self.history.save(self.data_file, self.memory)
        except OSError as e:
            self.logger.warning(f"Warning: could not save memory: {e}")
        self.logger.info("Memory cleared")
