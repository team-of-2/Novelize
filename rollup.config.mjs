import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import copy from 'rollup-plugin-copy';
import json from '@rollup/plugin-json';
import { visualizer } from "rollup-plugin-visualizer";

export default {
  input: 'sidepanel/index.js',
  output: {
    dir: 'dist/sidepanel',
    format: 'es', // Switch to ES module format
  },
  external: ['@aws-sdk/client-bedrock-runtime'],
  plugins: [
    commonjs(),
    nodeResolve(),
    json(),
    visualizer({ filename: "./dist/dependency-graph.html" }),
    copy({
      targets: [
        {
          src: ['manifest.json', 'background.js', 'sidepanel', 'images'],
          dest: 'dist',
        },
      ],
    }),
  ],
  onwarn(warning, warn) {
    if (warning.code === 'CIRCULAR_DEPENDENCY') {
      console.warn(`Circular dependency detected: ${warning.cycle ? warning.cycle.join(' -> ') : warning.importer}`);
    } else {
      warn(warning);
    }
  },
};
