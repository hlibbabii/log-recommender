private void sink() {
        int k = 1;
        while (2 * k <= this.size || 2 * k + 1 <= this.size) {
            int minIndex;
            if (this.heap[2 * k] >= this.heap[k]) {
                if (2 * k + 1 <= this.size && this.heap[2 * k + 1] >= this.heap[k]) {
                    break;
                } else if (2 * k + 1 > this.size) {
                    break;
                }
            }