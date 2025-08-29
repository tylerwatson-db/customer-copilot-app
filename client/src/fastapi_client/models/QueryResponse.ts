/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QueryMetadata } from './QueryMetadata';
/**
 * Response model for customer copilot queries.
 */
export type QueryResponse = {
    response: string;
    metadata: QueryMetadata;
    toolsUsed?: Array<string>;
    error?: (string | null);
};

