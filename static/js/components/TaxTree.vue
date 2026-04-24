<template>
  <ul class="taxtree">
    <li
      v-for="node in nodes"
      :key="node.id"
      class="tax-item"
      :class="{ 'is-checked': isChecked(node.id), 'is-open': isOpen(node.id) }"
    >
      <div class="tax-row">
        <button
          type="button"
          class="tax-toggle"
          :class="{ 'is-leaf': !node.children.length }"
          :aria-expanded="String(isOpen(node.id))"
          @click="toggle(node.id)"
        >
          <svg
            v-if="node.children.length"
            class="chev"
            :class="{ open: isOpen(node.id) }"
            width="8" height="8" viewBox="0 0 8 8" aria-hidden="true"
          >
            <path d="M2 1 L6 4 L2 7"
                  fill="none" stroke="currentColor"
                  stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span v-else class="chev-spacer" aria-hidden="true"></span>
        </button>

        <label class="tax-label">
          <input
            type="checkbox"
            class="tax-check"
            :checked="isChecked(node.id)"
            @change.stop="onToggleCheck(node)"
          />
          <span class="tax-name">{{ node.name }}</span>
          <span class="tax-level">{{ node.level }}</span>
        </label>
      </div>

      <TaxTree
        v-if="node.children.length && isOpen(node.id)"
        :nodes="node.children"
        :checked-ids="checkedIds"
        :open-ids="openIds"
        @check="$emit('check', $event)"
        @toggle="$emit('toggle', $event)"
      />
    </li>
  </ul>
</template>

<script>
export default {
  name: 'TaxTree',
  props: {
    nodes: { type: Array, required: true },
    checkedIds: { type: Array, required: true },
    openIds: { type: Array, required: true },
  },
  methods: {
    isOpen(id) { return this.openIds.includes(id); },
    isChecked(id) { return this.checkedIds.includes(id); },
    toggle(id) { this.$emit('toggle', id); },
    onToggleCheck(node) { this.$emit('check', node); },
  },
};
</script>

<style scoped>
/* ───────────────────────────────────────────────────────────
   TaxTree — recursive hierarchy with reliable elbow connectors.
   Descendant selector `.taxtree .taxtree` catches the nested
   <ul> regardless of how deep recursion goes. Vue 2's scoped
   CSS applies the SAME data-v id across every recursive
   instance of this component, so the selector traverses
   cleanly.
   ─────────────────────────────────────────────────────────── */
.taxtree {
  list-style: none;
  margin: 0;
  padding: 0;
  font-family: 'IBM Plex Sans', ui-sans-serif, -apple-system, sans-serif;
  color: #1f1b2e;
}

/* Only NESTED lists get indentation + a vertical guide line */
.taxtree .taxtree {
  margin-left: 9px;
  padding-left: 16px;
  border-left: 1px solid #d9d1ee;
}

.tax-item {
  position: relative;
}

/* Horizontal elbow tick reaching from the vertical guide to each row */
.taxtree .taxtree > .tax-item::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 14px;
  width: 12px;
  height: 1px;
  background: #d9d1ee;
}

/* Terminate the vertical guide flush under the last child.
   A 2px-wide white strip covers the parent's border-left that
   would otherwise extend past the last sibling. */
.taxtree .taxtree > .tax-item:last-child::after {
  content: '';
  position: absolute;
  left: -17px;
  top: 14px;
  bottom: 0;
  width: 2px;
  background: #ffffff;
}

/* ─── Row ─────────────────────────────────────────────── */
.tax-row {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 26px;
  padding: 2px 6px 2px 2px;
  border-radius: 3px;
  transition: background 0.12s ease;
  position: relative;
}
.tax-row:hover {
  background: #f5f1fc;
}
.is-checked > .tax-row {
  background: linear-gradient(to right,
                              rgba(245, 241, 252, 0) 0%,
                              rgba(245, 241, 252, 1) 18%);
}

/* ─── Chevron toggle ──────────────────────────────────── */
.tax-toggle {
  appearance: none;
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  cursor: pointer;
  color: #9d8bd4;
  width: 14px;
  height: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.tax-toggle.is-leaf {
  cursor: default;
  color: transparent;
}

.chev { transition: transform 0.14s cubic-bezier(0.4, 0, 0.2, 1); }
.chev.open { transform: rotate(90deg); }
.chev-spacer {
  display: inline-block;
  width: 8px;
  height: 8px;
}

/* ─── Label + checkbox + name + level ─────────────────── */
.tax-label {
  display: flex;
  align-items: baseline;
  gap: 7px;
  cursor: pointer;
  font-size: 13px;
  user-select: none;
  padding-right: 4px;
  flex: 0 0 auto;
  white-space: nowrap;
}
.tax-check {
  accent-color: #9d8bd4;
  margin: 0;
  flex-shrink: 0;
  transform: translateY(2px);
  cursor: pointer;
  width: 13px;
  height: 13px;
}
.tax-name {
  font-weight: 450;
  color: #1f1b2e;
  white-space: nowrap;
  letter-spacing: -0.002em;
}
.is-checked .tax-name {
  color: #6b4fb7;
  font-weight: 500;
}
.tax-level {
  font-family: 'Fraunces', Georgia, serif;
  font-style: italic;
  font-size: 10.5px;
  color: #a5a1b4;
  letter-spacing: 0.02em;
  flex-shrink: 0;
  font-variation-settings: 'opsz' 14;
  font-weight: 350;
}
</style>
