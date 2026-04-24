<template>
  <ul class="taxtree-list">
    <li v-for="node in nodes" :key="node.id" class="taxtree-node">
      <div class="taxtree-row">
        <button
          type="button"
          class="taxtree-toggle"
          :class="{ 'is-leaf': !node.children.length }"
          @click="toggle(node.id)"
          :aria-expanded="isOpen(node.id)"
        >
          <span v-if="node.children.length" class="chev" :class="{ open: isOpen(node.id) }">▸</span>
          <span v-else class="chev-spacer"></span>
        </button>
        <label class="taxtree-label">
          <input
            type="checkbox"
            :checked="isChecked(node.id)"
            @change="onToggleCheck(node)"
          />
          <span class="taxtree-name">{{ node.name }}</span>
          <span class="taxtree-level">{{ node.level }}</span>
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
.taxtree-list {
  list-style: none;
  margin: 0;
  padding-left: 42px;
  position: relative;
}
.taxtree-list::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #c8bbe8 0%, #efedf7 100%);
  border-radius: 2px;
}
.taxtree-list:first-of-type { padding-left: 0; }
.taxtree-list:first-of-type::before { display: none; }

.taxtree-node { margin: 8px 0; position: relative; }

.taxtree-node::before {
  content: '';
  position: absolute;
  left: -32px;
  top: 11px;
  width: 22px;
  height: 2px;
  background: #d8d0ea;
  border-radius: 2px;
}
.taxtree-list:first-of-type > .taxtree-node::before { display: none; }

.taxtree-row { display: flex; align-items: center; gap: 8px; min-height: 24px; }

.taxtree-toggle {
  background: none;
  border: none;
  width: 16px;
  height: 16px;
  padding: 0;
  cursor: pointer;
  color: #6b647f;
  font-size: 11px;
}
.taxtree-toggle.is-leaf { cursor: default; }

.chev { display: inline-block; transition: transform 0.15s ease; }
.chev.open { transform: rotate(90deg); }
.chev-spacer { display: inline-block; width: 11px; }

.taxtree-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #1f1b2e;
}
.taxtree-label input[type='checkbox'] {
  accent-color: #9d8bd4;
}
.taxtree-name { font-weight: 500; }
.taxtree-level {
  font-size: 11px;
  color: #6b647f;
  font-style: italic;
}
</style>
