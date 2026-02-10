"""
Project Analysis & Optimization Page
Displays 3-tier intelligent project analysis with AI suggestions
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

st.set_page_config(
    page_title="Project Optimization - ATS Forge",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Project Analysis & Optimization")

# Check if project analysis exists in session state
if 'project_analysis' not in st.session_state or not st.session_state.project_analysis:
    st.warning("⚠️ No project analysis available")
    st.info("👈 Go to the main page and run an analysis first")
    st.stop()

proj_data = st.session_state.project_analysis

# Overall Summary
st.header("📊 Overall Project Score")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Overall Score", f"{proj_data.get('overall_score', 0)}/100")
with col2:
    st.metric("Total Projects", proj_data.get('total_projects', 0))
with col3:
    avg_relevance = proj_data.get('overall_score', 0)
    st.metric("Avg Relevance", f"{avg_relevance:.1f}%")

st.divider()

# Recommendations
if proj_data.get('recommendations'):
    st.header("💡 AI Recommendations")
    for rec in proj_data['recommendations']:
        st.markdown(f"• {rec}")
    st.divider()

# Individual project analysis
for idx, project in enumerate(proj_data.get('projects', []), 1):
    # Determine tier color
    relevance = project['relevance_score']
    if relevance >= 70:
        tier_emoji = "🟢"
        tier_label = "HIGHLY RELEVANT"
    elif relevance >= 30:
        tier_emoji = "🟡"
        tier_label = "MODERATELY RELEVANT"
    else:
        tier_emoji = "🔴"
        tier_label = "NOT RELEVANT"
    
    with st.expander(f"{tier_emoji} **Project {idx}: {project['title']}** ({tier_label} - {project['relevance_score']}/100)", expanded=(idx == 1)):
        
        # Project metadata
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption(f"**Duration:** {project.get('duration', 'Not specified')}")
            st.caption(f"**Tech/Course:** {project.get('tech_or_course', 'N/A')}")
        with col_b:
            st.caption(f"**Keyword Match:** {project['keyword_match_pct']:.1f}%")
            st.caption(f"**Matched Keywords:** {len(project.get('matched_keywords', []))}")
        
        # AI Overall Advice
        suggestions_data = project.get('suggestions', {})
        if isinstance(suggestions_data, dict):
            overall_advice = suggestions_data.get('overall_advice', '')
            recommendation = suggestions_data.get('recommendation', '')
            
            if overall_advice:
                if recommendation == 'keep_and_optimize':
                    st.success(f"✅ **AI Recommendation:** {overall_advice}")
                elif recommendation == 'enhance_with_features':
                    st.warning(f"⚠️ **AI Recommendation:** {overall_advice}")
                else:
                    st.error(f"🔴 **AI Recommendation:** {overall_advice}")
        
        # Keyword analysis
        if project.get('matched_keywords'):
            st.markdown("**✅ Matched JD Keywords:**")
            st.success(", ".join(project['matched_keywords'][:10]))
        
        if project.get('missing_keywords'):
            st.markdown("**⚠️ Missing JD Keywords:**")
            st.warning(", ".join(project['missing_keywords'][:10]))
        
        st.markdown("---")
        
        # Original bullets
        st.markdown("#### 📝 Current Bullets")
        for bullet in project['bullets']:
            st.markdown(f"• {bullet}")
        
        # AI Suggestions based on tier
        if isinstance(suggestions_data, dict):
            # Tier 1 & 2: Bullet improvements
            bullet_suggestions = suggestions_data.get('suggestions', [])
            if bullet_suggestions:
                st.markdown("#### ✨ AI-Optimized Suggestions")
                
                for sug_idx, suggestion in enumerate(bullet_suggestions, 1):
                    is_proposed = suggestion.get('is_proposed_addition', False)
                    
                    if is_proposed:
                        st.markdown(f"**💡 Proposed Addition {sug_idx}:** (Implement this feature first)")
                    else:
                        st.markdown(f"**Suggestion {sug_idx}:**")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown("*Original:*")
                        st.text_area(
                            f"orig_{idx}_{sug_idx}",
                            suggestion.get('original', ''),
                            height=80,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    with col2:
                        st.markdown("*Improved:*")
                        st.text_area(
                            f"improved_{idx}_{sug_idx}",
                            suggestion.get('improved', ''),
                            height=80,
                            key=f"improved_text_{idx}_{sug_idx}",
                            label_visibility="collapsed"
                        )
                    
                    # Show what was added
                    if suggestion.get('added_keywords'):
                        st.caption(f"✅ Added keywords: {', '.join(suggestion['added_keywords'])}")
                    if suggestion.get('improvement_reason'):
                        st.caption(f"💡 {suggestion['improvement_reason']}")
                    
                    st.markdown("---")
            
            # Tier 2: Feature additions
            feature_additions = suggestions_data.get('feature_additions', [])
            if feature_additions:
                st.markdown("#### 🚀 Suggested Feature Additions")
                st.info("These are small features you can add to improve JD alignment:")
                
                for feat_idx, feature in enumerate(feature_additions, 1):
                    st.markdown(f"**Feature {feat_idx}: {feature.get('feature', 'N/A')}**")
                    st.markdown(f"- **Tech Stack:** {feature.get('tech_stack', 'N/A')}")
                    st.markdown(f"- **Why:** {feature.get('reason', 'N/A')}")
                    st.markdown(f"- **Effort:** {feature.get('estimated_effort', 'N/A')}")
                    st.markdown("")
            
            # Tier 3: Alternative projects
            alternative_projects = suggestions_data.get('alternative_projects', [])
            if alternative_projects:
                st.markdown("#### 🔄 Alternative Project Suggestions")
                st.warning("This project has low JD alignment. Consider these alternatives:")
                
                for alt_idx, alt_proj in enumerate(alternative_projects, 1):
                    st.markdown(f"**Alternative {alt_idx}: {alt_proj.get('title', 'N/A')}**")
                    st.markdown(f"- **Description:** {alt_proj.get('description', 'N/A')}")
                    st.markdown(f"- **Technologies:** {', '.join(alt_proj.get('key_technologies', []))}")
                    st.markdown(f"- **Expected Impact:** {alt_proj.get('expected_impact', 'N/A').upper()}")
                    st.markdown("")
            
            # Copy-paste optimized version (only for Tier 1 & 2)
            if bullet_suggestions and recommendation != 'consider_replacing':
                st.markdown("#### 📋 Copy-Paste Optimized Version")
                optimized_bullets = "\n".join([f"- {sug.get('improved', '')}" for sug in bullet_suggestions])
                optimized_project = f"""**{project['title']}** | {project.get('tech_or_course', 'Technology')}
{project.get('duration', 'Month/Year - Month/Year')}

{optimized_bullets}
"""
                st.code(optimized_project, language="markdown")
                
                if any(sug.get('is_proposed_addition') for sug in bullet_suggestions):
                    st.caption("⚠️ **Note:** Some suggestions are proposed additions. Implement these features before using in your resume.")
                else:
                    st.caption("👆 Copy this optimized version to your resume")
