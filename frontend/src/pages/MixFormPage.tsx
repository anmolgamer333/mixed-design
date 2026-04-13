import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { MixDesign } from "../types";

interface FormState {
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
  final_batch_water_kg: number;
  final_batch_cement_kg: number;
  final_batch_fine_agg_kg: number;
  final_batch_coarse_agg_kg: number;
  mix_proportion_by_weight: string;
  assumptions: string;
  remarks: string;
  category: string;
}

const defaultState: FormState = {
  mix_id: "",
  slug: "",
  mix_name: "",
  project_tag: "general",
  concrete_grade: "M30",
  target_mean_strength: 38,
  design_method: "IS 10262:2019",
  cement_type: "OPC 53",
  max_aggregate_size_mm: 20,
  exposure_condition: "Moderate",
  slump_mm: 100,
  water_cement_ratio: 0.45,
  water_content_kg_m3: 180,
  cement_content_kg_m3: 400,
  fine_agg_content_kg_m3: 680,
  coarse_agg_content_kg_m3: 1150,
  admixture_type: "PCE Superplasticizer",
  admixture_dosage_pct: 0.8,
  final_batch_water_kg: 180,
  final_batch_cement_kg: 400,
  final_batch_fine_agg_kg: 680,
  final_batch_coarse_agg_kg: 1150,
  mix_proportion_by_weight: "1:1.7:2.8 (w/c=0.45)",
  assumptions: "",
  remarks: "",
  category: "design mix"
};

export function MixFormPage() {
  const [form, setForm] = useState<FormState>(defaultState);
  const navigate = useNavigate();
  const { slug } = useParams();
  const isEdit = Boolean(slug);

  useEffect(() => {
    if (!isEdit) return;
    api.get<MixDesign>(`/mixes/${slug}`).then((res) => {
      const m = res.data;
      setForm({
        mix_id: m.mix_id,
        slug: m.slug,
        mix_name: m.mix_name,
        project_tag: m.project_tag,
        concrete_grade: m.concrete_grade,
        target_mean_strength: m.target_mean_strength,
        design_method: m.design_method,
        cement_type: m.cement_type,
        max_aggregate_size_mm: m.max_aggregate_size_mm,
        exposure_condition: m.exposure_condition,
        slump_mm: m.slump_mm,
        water_cement_ratio: m.water_cement_ratio,
        water_content_kg_m3: m.water_content_kg_m3,
        cement_content_kg_m3: m.cement_content_kg_m3,
        fine_agg_content_kg_m3: m.fine_agg_content_kg_m3,
        coarse_agg_content_kg_m3: m.coarse_agg_content_kg_m3,
        admixture_type: m.admixture_type,
        admixture_dosage_pct: m.admixture_dosage_pct,
        final_batch_water_kg: m.final_batch_water_kg,
        final_batch_cement_kg: m.final_batch_cement_kg,
        final_batch_fine_agg_kg: m.final_batch_fine_agg_kg,
        final_batch_coarse_agg_kg: m.final_batch_coarse_agg_kg,
        mix_proportion_by_weight: m.mix_proportion_by_weight,
        assumptions: m.assumptions,
        remarks: m.remarks,
        category: m.category
      });
    });
  }, [isEdit, slug]);

  const setField = (key: keyof FormState, value: string | number) => setForm((prev) => ({ ...prev, [key]: value }));

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const payload = {
      ...form,
      quantity_basis: "Per 1 m3",
      moisture_correction_fine_pct: 0,
      moisture_correction_coarse_pct: 0,
      absorption_fine_pct: 0,
      absorption_coarse_pct: 0,
      field_water_adjustment_kg: 0,
      sg_cement: 3.15,
      sg_fine_agg: 2.65,
      sg_coarse_agg: 2.70,
      sg_admixture: 1.1,
      status: "draft",
      is_public: false
    };

    if (isEdit) {
      await api.put(`/mixes/${slug}`, payload);
      navigate(`/mixes/${slug}`);
      return;
    }

    await api.post("/mixes", payload);
    navigate("/mixes");
  };

  return (
    <form className="card" onSubmit={onSubmit}>
      <h3>{isEdit ? "Edit Mix Design" : "Add New Mix Design"}</h3>
      <div className="grid-4">
        <input value={form.mix_id} onChange={(e) => setField("mix_id", e.target.value)} placeholder="Mix ID" required />
        <input value={form.slug} onChange={(e) => setField("slug", e.target.value)} placeholder="Slug" required />
        <input value={form.mix_name} onChange={(e) => setField("mix_name", e.target.value)} placeholder="Mix Name" required />
        <input value={form.project_tag} onChange={(e) => setField("project_tag", e.target.value)} placeholder="Project Tag" />
      </div>
      <div className="grid-4" style={{ marginTop: 10 }}>
        <input value={form.concrete_grade} onChange={(e) => setField("concrete_grade", e.target.value)} placeholder="Grade" />
        <input type="number" value={form.target_mean_strength} onChange={(e) => setField("target_mean_strength", Number(e.target.value))} placeholder="Target Mean Strength" />
        <input value={form.design_method} onChange={(e) => setField("design_method", e.target.value)} placeholder="Method" />
        <input value={form.cement_type} onChange={(e) => setField("cement_type", e.target.value)} placeholder="Cement Type" />
      </div>
      <div className="grid-4" style={{ marginTop: 10 }}>
        <input type="number" value={form.slump_mm} onChange={(e) => setField("slump_mm", Number(e.target.value))} placeholder="Slump mm" />
        <input type="number" value={form.water_cement_ratio} step="0.01" onChange={(e) => setField("water_cement_ratio", Number(e.target.value))} placeholder="w/c" />
        <input type="number" value={form.water_content_kg_m3} onChange={(e) => setField("water_content_kg_m3", Number(e.target.value))} placeholder="Water kg/m3" />
        <input type="number" value={form.cement_content_kg_m3} onChange={(e) => setField("cement_content_kg_m3", Number(e.target.value))} placeholder="Cement kg/m3" />
      </div>
      <div className="grid-4" style={{ marginTop: 10 }}>
        <input type="number" value={form.fine_agg_content_kg_m3} onChange={(e) => setField("fine_agg_content_kg_m3", Number(e.target.value))} placeholder="Fine agg kg/m3" />
        <input type="number" value={form.coarse_agg_content_kg_m3} onChange={(e) => setField("coarse_agg_content_kg_m3", Number(e.target.value))} placeholder="Coarse agg kg/m3" />
        <input value={form.admixture_type} onChange={(e) => setField("admixture_type", e.target.value)} placeholder="Admixture type" />
        <input type="number" step="0.01" value={form.admixture_dosage_pct} onChange={(e) => setField("admixture_dosage_pct", Number(e.target.value))} placeholder="Dosage %" />
      </div>
      <textarea value={form.mix_proportion_by_weight} onChange={(e) => setField("mix_proportion_by_weight", e.target.value)} style={{ marginTop: 10 }} />
      <textarea value={form.assumptions} onChange={(e) => setField("assumptions", e.target.value)} placeholder="Assumptions" style={{ marginTop: 10 }} />
      <textarea value={form.remarks} onChange={(e) => setField("remarks", e.target.value)} placeholder="Remarks" style={{ marginTop: 10 }} />
      <div className="actions" style={{ marginTop: 12 }}>
        <button className="btn" type="submit">{isEdit ? "Save Changes" : "Add Mix"}</button>
      </div>
    </form>
  );
}
