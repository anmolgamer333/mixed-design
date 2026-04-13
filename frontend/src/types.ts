export type MixStatus = "draft" | "approved" | "trial" | "archived";

export interface MixDesign {
  id: number;
  mix_id: string;
  slug: string;
  mix_name: string;
  project_tag: string;
  concrete_grade: string;
  target_mean_strength: number;
  design_method: string;
  cement_type: string;
  max_aggregate_size_mm: number;
  exposure_condition: string;
  slump_mm: number;
  water_cement_ratio: number;
  water_content_kg_m3: number;
  cement_content_kg_m3: number;
  fine_agg_content_kg_m3: number;
  coarse_agg_content_kg_m3: number;
  admixture_type: string;
  admixture_dosage_pct: number;
  moisture_correction_fine_pct: number;
  moisture_correction_coarse_pct: number;
  absorption_fine_pct: number;
  absorption_coarse_pct: number;
  field_water_adjustment_kg: number;
  final_batch_water_kg: number;
  final_batch_cement_kg: number;
  final_batch_fine_agg_kg: number;
  final_batch_coarse_agg_kg: number;
  mix_proportion_by_weight: string;
  quantity_basis: string;
  assumptions: string;
  remarks: string;
  category: string;
  status: MixStatus;
  is_public: boolean;
  qr_path_png: string;
  qr_path_svg: string;
  download_ref: string;
  created_at: string;
  updated_at: string;
}

export interface MixListResponse {
  total: number;
  items: MixDesign[];
}
